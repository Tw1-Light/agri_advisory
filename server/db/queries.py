import json
from datetime import date, datetime, time

from sqlalchemy import and_, desc
from sqlalchemy.orm import Session

from server.db.models import Farm, SensorImageLog


def get_farm_by_id(db: Session, farm_id: str) -> Farm | None:
    return db.query(Farm).filter(Farm.farm_id == farm_id).first()


def create_farm(db: Session, farm_data: dict) -> Farm:
    farm = Farm(**farm_data)
    db.add(farm)
    db.commit()
    db.refresh(farm)
    return farm


def update_farm_sensors(db: Session, farm_id: str, sensors: dict, sensor_timestamp: datetime) -> Farm | None:
    farm = get_farm_by_id(db, farm_id)
    if not farm:
        return None
    farm.moisture = sensors["moisture"]
    farm.ph = sensors["ph"]
    farm.N = sensors["N"]
    farm.P = sensors["P"]
    farm.K = sensors["K"]
    farm.sensor_timestamp = sensor_timestamp
    db.commit()
    db.refresh(farm)
    return farm


def insert_log_row(db: Session, **kwargs) -> int:
    log = SensorImageLog(**kwargs)
    db.add(log)
    db.commit()
    db.refresh(log)
    return log.id


def get_today_am_row(db: Session, farm_id: str, today_date: date) -> SensorImageLog | None:
    start_dt = datetime.combine(today_date, time.min)
    end_dt = datetime.combine(today_date, time.max)
    return (
        db.query(SensorImageLog)
        .filter(
            and_(
                SensorImageLog.farm_id == farm_id,
                SensorImageLog.run_type == "am",
                SensorImageLog.logged_at >= start_dt,
                SensorImageLog.logged_at <= end_dt,
            )
        )
        .order_by(desc(SensorImageLog.logged_at))
        .first()
    )


def get_latest_pm_next_cycle_flags(db: Session, farm_id: str) -> list[str]:
    row = (
        db.query(SensorImageLog)
        .filter(
            and_(SensorImageLog.farm_id == farm_id, SensorImageLog.run_type == "pm")
        )
        .order_by(desc(SensorImageLog.logged_at))
        .first()
    )
    if not row or not row.next_cycle_flags:
        return []
    try:
        value = json.loads(row.next_cycle_flags)
        return value if isinstance(value, list) else []
    except json.JSONDecodeError:
        return []


def get_latest_advisory(db: Session, farm_id: str, run_type: str | None = None) -> SensorImageLog | None:
    query = db.query(SensorImageLog).filter(SensorImageLog.farm_id == farm_id)
    if run_type:
        query = query.filter(SensorImageLog.run_type == run_type)
    return query.order_by(desc(SensorImageLog.logged_at)).first()
