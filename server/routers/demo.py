from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from server.data.demo_scenarios import SCENARIOS
from server.db import queries
from server.db.database import get_db
from server.engines.stage_engine import compute_stage
from server.schemas import ScenarioLoadRequest


router = APIRouter(tags=["demo"])


@router.get("/demo/controller")
def demo_controller():
    return FileResponse("demo/index.html")


@router.get("/demo/scenarios")
def list_scenarios():
    return {"scenarios": list(SCENARIOS.values())}


@router.post("/demo/load-scenario")
def load_scenario(payload: ScenarioLoadRequest, db: Session = Depends(get_db)):
    if payload.scenario_id not in {"SC-02", "SC-03", "SC-04"}:
        raise HTTPException(status_code=422, detail="Invalid scenario_id")

    scenario = SCENARIOS[payload.scenario_id]
    farm = queries.get_farm_by_id(db, payload.farm_id)
    if farm is None:
        raise HTTPException(status_code=404, detail="Farm not found")

    today = date.today()
    now = datetime.utcnow()
    planting_date = today - timedelta(days=scenario["target_day"])

    farm.planting_date = planting_date
    farm.moisture = scenario["am_sensors"]["moisture"]
    farm.ph = scenario["am_sensors"]["ph"]
    farm.N = scenario["am_sensors"]["N"]
    farm.P = scenario["am_sensors"]["P"]
    farm.K = scenario["am_sensors"]["K"]
    farm.image_path = f"/static/{scenario['image_file']}"
    farm.image_timestamp = now - timedelta(hours=1)
    farm.sensor_timestamp = now - timedelta(minutes=10)

    db.commit()
    db.refresh(farm)

    stage = compute_stage(farm, today)
    return {
        "scenario_id": payload.scenario_id,
        "farm_id": payload.farm_id,
        "computed_day": stage["days_elapsed"],
        "phase": stage["phase"],
        "phase_name": stage["phase_name"],
        "planting_date": str(planting_date),
        "image_path": farm.image_path,
        "image_timestamp": farm.image_timestamp.isoformat() + "Z",
    }


@router.get("/demo/status")
def demo_status(farm_id: str, db: Session = Depends(get_db)):
    farm = queries.get_farm_by_id(db, farm_id)
    if farm is None:
        raise HTTPException(status_code=404, detail="Farm not found")

    stage = compute_stage(farm, date.today())
    latest = queries.get_latest_advisory(db, farm_id)

    return {
        "farm_id": farm.farm_id,
        "crop": farm.crop,
        "stage": stage,
        "sensors": {
            "moisture": farm.moisture,
            "ph": farm.ph,
            "N": farm.N,
            "P": farm.P,
            "K": farm.K,
            "sensor_timestamp": farm.sensor_timestamp.isoformat() + "Z" if farm.sensor_timestamp else None,
        },
        "last_advisory": {
            "run_type": latest.run_type if latest else None,
            "logged_at": latest.logged_at.isoformat() + "Z" if latest else None,
        },
    }
