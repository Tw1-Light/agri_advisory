from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field


class LocationPayload(BaseModel):
    state: str
    district: str
    commodity: str
    lat: float
    lon: float


class FarmRegistrationRequest(BaseModel):
    farm_id: str
    crop: str
    planting_date: date
    language: str
    location: LocationPayload


class SensorPayload(BaseModel):
    moisture: float
    ph: float
    N: float
    P: float
    K: float


class SensorUpdateRequest(BaseModel):
    farm_id: str
    sensors: SensorPayload
    sensor_timestamp: datetime


class TriggerRequest(BaseModel):
    farm_id: str


class ScenarioLoadRequest(BaseModel):
    scenario_id: str
    farm_id: str


class RegisterResponse(BaseModel):
    farm_id: str
    status: str


class SensorUpdateResponse(BaseModel):
    farm_id: str
    status: str
    anomalies: list[str] = Field(default_factory=list)


class GenericDictResponse(BaseModel):
    data: dict[str, Any]
