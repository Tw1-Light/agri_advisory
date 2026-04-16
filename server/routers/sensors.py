from datetime import timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from server.db import queries
from server.db.database import get_db
from server.engines.confidence import run_plausibility_checks
from server.schemas import SensorUpdateRequest, SensorUpdateResponse


router = APIRouter(tags=["sensors"])


@router.post("/sensor-update", response_model=SensorUpdateResponse)
def sensor_update(payload: SensorUpdateRequest, db: Session = Depends(get_db)):
    farm = queries.get_farm_by_id(db, payload.farm_id)
    if farm is None:
        raise HTTPException(status_code=404, detail="Farm not found")

    sensors = payload.sensors.model_dump()
    required_fields = ["moisture", "ph", "N", "P", "K"]
    for field in required_fields:
        if field not in sensors:
            raise HTTPException(status_code=400, detail=f"Missing sensor field: {field}")

    if not (0 <= sensors["moisture"] <= 100):
        raise HTTPException(status_code=400, detail="moisture must be in 0-100")
    if not (0 <= sensors["ph"] <= 14):
        raise HTTPException(status_code=400, detail="ph must be in 0-14")
    for nutrient in ["N", "P", "K"]:
        if not (0 <= sensors[nutrient] <= 999):
            raise HTTPException(status_code=400, detail=f"{nutrient} must be in 0-999")

    ts = payload.sensor_timestamp
    if ts.tzinfo is None or ts.utcoffset() != timezone.utc.utcoffset(ts):
        raise HTTPException(status_code=400, detail="sensor_timestamp must be UTC")

    anomalies = run_plausibility_checks(sensors)
    updated = queries.update_farm_sensors(
        db,
        farm_id=payload.farm_id,
        sensors=sensors,
        sensor_timestamp=payload.sensor_timestamp.replace(tzinfo=None),
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="Farm not found")

    return SensorUpdateResponse(
        farm_id=payload.farm_id,
        status="sensor_updated",
        anomalies=anomalies,
    )
