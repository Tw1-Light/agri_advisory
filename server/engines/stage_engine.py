from datetime import date, timedelta

from server.data.lifecycle_reference import LIFECYCLE


def compute_stage(farm, today: date) -> dict:
    crop = (farm.crop or "").lower()
    phases = LIFECYCLE.get(crop)
    if not phases:
        return {
            "phase": 1,
            "phase_name": "Unknown",
            "days_elapsed": 0,
            "days_into_phase": 0,
            "days_remaining_in_phase": 0,
            "stage_source": "computed",
            "mandi_active": False,
            "npk_targets": {"N": 0, "P": 0, "K": 0},
            "water_target": "unknown",
            "visual_indicators": [],
        }

    stage_source = "computed"
    if farm.stage_override is not None and farm.stage_override_date is not None:
        delta = (today - farm.stage_override_date).days
        if delta <= 30:
            idx = max(0, min(len(phases) - 1, int(farm.stage_override) - 1))
            phase_midpoint = phases[idx]["midpoint_day"]
            adjusted_anchor = farm.stage_override_date - timedelta(days=phase_midpoint)
            days_elapsed = (today - adjusted_anchor).days
            stage_source = "farmer_override"
        else:
            days_elapsed = (today - farm.planting_date).days
    else:
        days_elapsed = (today - farm.planting_date).days

    days_elapsed = max(days_elapsed, 0)
    selected = phases[-1]
    for phase in phases:
        if days_elapsed <= phase["end_day"]:
            selected = phase
            break

    days_into_phase = max(0, days_elapsed - selected["start_day"])
    days_remaining = max(0, selected["end_day"] - days_elapsed)

    return {
        "phase": selected["phase"],
        "phase_name": selected["phase_name"],
        "days_elapsed": days_elapsed,
        "days_into_phase": days_into_phase,
        "days_remaining_in_phase": days_remaining,
        "stage_source": stage_source,
        "mandi_active": selected["mandi_active"],
        "npk_targets": selected["npk_targets"],
        "water_target": selected["water_target"],
        "visual_indicators": selected["visual_indicators"],
    }
