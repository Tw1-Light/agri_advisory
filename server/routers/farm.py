from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from server.db.database import get_db
from server.db import queries
from server.schemas import FarmRegistrationRequest, RegisterResponse


router = APIRouter(tags=["farm"])

ALLOWED_CROPS = {"rice", "wheat", "maize"}


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=RegisterResponse)
def register_farm(payload: FarmRegistrationRequest, db: Session = Depends(get_db)):
    crop = payload.crop.lower().strip()
    if crop not in ALLOWED_CROPS:
        raise HTTPException(status_code=422, detail="crop must be rice, wheat, or maize")

    if payload.planting_date > date.today():
        raise HTTPException(status_code=422, detail="planting_date cannot be in the future")

    if not (6.0 <= payload.location.lat <= 37.0):
        raise HTTPException(status_code=422, detail="lat out of bounds")

    if not (68.0 <= payload.location.lon <= 97.5):
        raise HTTPException(status_code=422, detail="lon out of bounds")

    existing = queries.get_farm_by_id(db, payload.farm_id)
    if existing:
        raise HTTPException(status_code=409, detail="farm_id already exists")

    queries.create_farm(
        db,
        {
            "farm_id": payload.farm_id,
            "crop": crop,
            "planting_date": payload.planting_date,
            "language": payload.language,
            "state": payload.location.state,
            "district": payload.location.district,
            "commodity": payload.location.commodity,
            "lat": payload.location.lat,
            "lon": payload.location.lon,
        },
    )

    return RegisterResponse(farm_id=payload.farm_id, status="registered")
