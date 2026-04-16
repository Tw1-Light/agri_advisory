import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from server.db import queries
from server.db.database import get_db
from server.pipeline.pipeline_runner import run_am_pipeline, run_pm_pipeline
from server.schemas import TriggerRequest


router = APIRouter(tags=["advisory"])


@router.post("/trigger/am")
async def trigger_am(payload: TriggerRequest, db: Session = Depends(get_db)):
    return await run_am_pipeline(db, payload.farm_id)


@router.post("/trigger/pm")
async def trigger_pm(payload: TriggerRequest, db: Session = Depends(get_db)):
    return await run_pm_pipeline(db, payload.farm_id)


@router.get("/latest-advisory")
def latest_advisory(farm_id: str, run_type: str | None = None, db: Session = Depends(get_db)):
    if run_type and run_type not in {"am", "pm"}:
        raise HTTPException(status_code=422, detail="run_type must be am or pm")

    row = queries.get_latest_advisory(db, farm_id=farm_id, run_type=run_type)
    if row is None:
        raise HTTPException(status_code=404, detail="No advisory found")

    data = row.advisory_json if row.run_type == "am" else row.diagnostic_json
    if not data:
        raise HTTPException(status_code=404, detail="No advisory payload found")

    try:
        return json.loads(data)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Stored advisory payload is corrupted")
