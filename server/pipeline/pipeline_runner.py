import json
from datetime import date, datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from server.agents.mandi_gate import check_mandi
from server.agents.weather import fetch_weather
from server.db import queries
from server.engines.confidence import compute_confidence, run_plausibility_checks
from server.engines.image_validator import validate_image
from server.engines.outcome_diff import compute_outcome_diff
from server.engines.stage_engine import compute_stage
from server.pipeline.orchestrator import (
    build_am_prompt,
    build_pm_prompt,
    call_gemini_am,
    call_gemini_pm,
)
from server.translation.sarvam import translate


IST_OFFSET = timedelta(hours=5, minutes=30)


def _iso_utc(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _to_ist(dt: datetime) -> datetime:
    return dt.astimezone(timezone(IST_OFFSET))


def _sensors_from_farm(farm) -> dict:
    return {
        "moisture": farm.moisture,
        "ph": farm.ph,
        "N": farm.N,
        "P": farm.P,
        "K": farm.K,
    }


def _default_am_json(confidence_label: str, mandi_active: bool) -> dict:
    return {
        "confidence": confidence_label,
        "primary_stress": "Nutrient and moisture imbalance risk",
        "root_cause": "Sensor pattern indicates mild imbalance in current phase",
        "actions": {
            "today": "Apply only phase-aligned irrigation and nutrient correction.",
            "this_week": "Recheck sensors after 48-72 hours.",
            "avoid": "Avoid over-application of inputs today.",
        },
        "sensor_flags": None,
        "stage_mismatch": None,
        "advisory_text": "Crop condition is manageable. Follow phase-aligned corrections and monitor progress.",
        "recheck_in_days": 7,
        "mandi_advice": "Monitor mandi trend before planning sale." if mandi_active else None,
    }


def _default_pm_json(deviation_flags: list[str]) -> dict:
    return {
        "outcome_verified": len(deviation_flags) == 0,
        "verification_summary": "Evening sensors align with expected direction." if len(deviation_flags) == 0 else "One or more targeted fields did not move as expected.",
        "deviations_detected": deviation_flags,
        "new_risks": [],
        "next_cycle_flags": [f"review_{flag}" for flag in deviation_flags],
        "diagnostic_text": "Evening diagnostic generated from AM-to-PM sensor comparison.",
    }


def assemble_am_response(farm, stage, gemini_json, weather, mandi_data, confidence, image_status, advisory_regional, next_flags, now_ist) -> dict:
    return {
        "run_type": "am",
        "generated_at": _iso_utc(now_ist),
        "next_advisory_at": _iso_utc(now_ist + timedelta(hours=12)),
        "crop_stage": {
            "phase": stage["phase"],
            "phase_name": stage["phase_name"],
            "days_elapsed": stage["days_elapsed"],
            "days_into_phase": stage["days_into_phase"],
            "days_remaining_in_phase": stage["days_remaining_in_phase"],
            "stage_source": stage["stage_source"],
            "mandi_active": stage["mandi_active"],
        },
        "image_status": image_status,
        "confidence_score": confidence["confidence_score"],
        "confidence_label": confidence["confidence_label"],
        "advisory_regional": advisory_regional,
        "weather": {"forecast_7d": weather or []},
        "price": None
        if not mandi_data
        else {
            "price_series": mandi_data["price_series"],
            "modal_price_latest": mandi_data["modal_price_latest"],
            "trend": mandi_data["trend"],
        },
        "next_cycle_flags": next_flags or [],
        "ai_recommendations": {
            "confidence": gemini_json.get("confidence") or confidence["confidence_label"],
            "primary_stress": gemini_json.get("primary_stress"),
            "root_cause": gemini_json.get("root_cause"),
            "actions": gemini_json.get("actions") or {},
            "sensor_flags": gemini_json.get("sensor_flags"),
            "stage_mismatch": gemini_json.get("stage_mismatch"),
            "advisory_text": gemini_json.get("advisory_text", ""),
            "recheck_in_days": gemini_json.get("recheck_in_days", 7),
            "mandi_advice": gemini_json.get("mandi_advice") if stage["mandi_active"] else None,
        },
    }


def assemble_pm_response(farm, stage, gemini_json, diff_result, diagnostic_regional, am_log_id, now_ist) -> dict:
    next_flags = gemini_json.get("next_cycle_flags")
    if not isinstance(next_flags, list):
        next_flags = []

    outcome_verified = gemini_json.get("outcome_verified")
    if not isinstance(outcome_verified, bool):
        outcome_verified = len(diff_result["deviation_flags"]) == 0

    deviations_detected = gemini_json.get("deviations_detected")
    if not isinstance(deviations_detected, list):
        deviations_detected = diff_result["deviation_flags"]

    verification_summary = gemini_json.get("verification_summary")
    if not isinstance(verification_summary, str) or not verification_summary.strip():
        verification_summary = (
            "Evening sensors align with expected direction."
            if outcome_verified
            else "One or more targeted fields did not move as expected."
        )

    return {
        "run_type": "pm",
        "generated_at": _iso_utc(now_ist),
        "am_log_id": am_log_id,
        "next_advisory_at": _iso_utc(now_ist + timedelta(hours=12)),
        "outcome_diff": diff_result["outcome_diff"],
        "deviation_flags": diff_result["deviation_flags"],
        "new_anomaly_flags": gemini_json.get("new_anomaly_flags", []),
        "diagnostic_regional": diagnostic_regional,
        "ai_diagnostic": {
            "outcome_verified": outcome_verified,
            "verification_summary": verification_summary,
            "deviations_detected": deviations_detected,
            "new_risks": gemini_json.get("new_risks", []),
            "next_cycle_flags": next_flags,
            "diagnostic_text": gemini_json.get("diagnostic_text", ""),
        },
    }


async def run_am_pipeline(db: Session, farm_id: str) -> dict:
    farm = queries.get_farm_by_id(db, farm_id)
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")

    now = datetime.now(timezone.utc)
    today = now.date()
    stage = compute_stage(farm, today)

    image_status = validate_image(farm.image_path, farm.image_timestamp, farm.sensor_timestamp, now.replace(tzinfo=None))
    weather = await fetch_weather(farm.lat, farm.lon)
    mandi_data = check_mandi(stage, farm.crop)

    sensors = _sensors_from_farm(farm)
    anomalies = run_plausibility_checks(sensors)
    present_sensor_count = len([v for v in sensors.values() if v is not None])

    if farm.sensor_timestamp is None:
        sensor_age = 999.0
    else:
        sensor_age = max(0.0, (now.replace(tzinfo=None) - farm.sensor_timestamp).total_seconds() / 3600.0)

    confidence = compute_confidence(
        farm=farm,
        image_status=image_status,
        weather_available=weather is not None,
        mandi_available=mandi_data is not None,
        mandi_active=stage["mandi_active"],
        anomaly_count=len(anomalies),
        sensor_age_hours=sensor_age,
        present_sensor_count=present_sensor_count,
    )

    next_flags = queries.get_latest_pm_next_cycle_flags(db, farm_id)

    prompt = build_am_prompt(stage, sensors, weather, mandi_data, confidence, next_flags, farm.image_path)
    try:
        gemini_json = call_gemini_am(prompt, farm.crop, stage["days_elapsed"], farm.image_path, stage["mandi_active"])
    except Exception:
        gemini_json = _default_am_json(confidence["confidence_label"], stage["mandi_active"])

    advisory_regional = await translate(gemini_json.get("advisory_text", ""), "en", farm.language)
    response = assemble_am_response(
        farm=farm,
        stage=stage,
        gemini_json=gemini_json,
        weather=weather,
        mandi_data=mandi_data,
        confidence=confidence,
        image_status=image_status,
        advisory_regional=advisory_regional,
        next_flags=next_flags,
        now_ist=_to_ist(now),
    )

    queries.insert_log_row(
        db,
        run_type="am",
        farm_id=farm_id,
        am_log_id=None,
        logged_at=now.replace(tzinfo=None),
        moisture=farm.moisture,
        ph=farm.ph,
        N=farm.N,
        P=farm.P,
        K=farm.K,
        sensor_timestamp=farm.sensor_timestamp,
        image_path=farm.image_path,
        image_timestamp=farm.image_timestamp,
        computed_stage=stage["phase"],
        stage_source=stage["stage_source"],
        confidence_score=confidence["confidence_score"],
        advisory_json=json.dumps(response),
        diagnostic_json=None,
        next_cycle_flags=None,
    )

    return response


async def run_pm_pipeline(db: Session, farm_id: str) -> dict:
    farm = queries.get_farm_by_id(db, farm_id)
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")

    now = datetime.now(timezone.utc)
    today = date.today()
    am_row = queries.get_today_am_row(db, farm_id, today)
    if am_row is None:
        raise HTTPException(status_code=404, detail="No AM advisory found for today")

    if farm.sensor_timestamp is None or am_row.sensor_timestamp is None or farm.sensor_timestamp <= am_row.sensor_timestamp:
        return {
            "run_type": "pm",
            "status": "skipped",
            "farm_id": farm_id,
            "reason": "no_post_action_sensor_data",
            "detail": "Evening sensor_timestamp not newer than morning. Update sensors before triggering PM.",
        }

    stage = compute_stage(farm, today)
    morning_sensors = {
        "moisture": am_row.moisture,
        "ph": am_row.ph,
        "N": am_row.N,
        "P": am_row.P,
        "K": am_row.K,
    }
    evening_sensors = _sensors_from_farm(farm)

    am_json = {}
    if am_row.advisory_json:
        try:
            am_json = json.loads(am_row.advisory_json)
        except json.JSONDecodeError:
            am_json = {}

    morning_actions = (am_json.get("ai_recommendations") or {}).get("actions")
    diff_result = compute_outcome_diff(morning_sensors, evening_sensors, morning_actions)
    new_anomaly_flags = run_plausibility_checks(evening_sensors)

    prompt = build_pm_prompt(am_json, morning_sensors, evening_sensors, diff_result["outcome_diff"], diff_result["deviation_flags"], stage)
    try:
        gemini_json = call_gemini_pm(prompt, farm.crop, stage["days_elapsed"])
    except Exception:
        gemini_json = _default_pm_json(diff_result["deviation_flags"])

    gemini_json["new_anomaly_flags"] = new_anomaly_flags
    if not isinstance(gemini_json.get("next_cycle_flags"), list):
        gemini_json["next_cycle_flags"] = []

    diagnostic_regional = await translate(gemini_json.get("diagnostic_text", ""), "en", farm.language)
    response = assemble_pm_response(
        farm=farm,
        stage=stage,
        gemini_json=gemini_json,
        diff_result=diff_result,
        diagnostic_regional=diagnostic_regional,
        am_log_id=am_row.id,
        now_ist=_to_ist(now),
    )

    queries.insert_log_row(
        db,
        run_type="pm",
        farm_id=farm_id,
        am_log_id=am_row.id,
        logged_at=now.replace(tzinfo=None),
        moisture=farm.moisture,
        ph=farm.ph,
        N=farm.N,
        P=farm.P,
        K=farm.K,
        sensor_timestamp=farm.sensor_timestamp,
        image_path=farm.image_path,
        image_timestamp=farm.image_timestamp,
        computed_stage=stage["phase"],
        stage_source=stage["stage_source"],
        confidence_score=None,
        advisory_json=None,
        diagnostic_json=json.dumps(response),
        next_cycle_flags=json.dumps(gemini_json.get("next_cycle_flags") or []),
    )

    return response
