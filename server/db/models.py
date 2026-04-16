from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from server.db.database import Base


class Farm(Base):
    __tablename__ = "farms"

    farm_id = Column(String, primary_key=True, index=True)
    crop = Column(String, nullable=False)
    planting_date = Column(Date, nullable=False)
    language = Column(String, nullable=False)
    state = Column(String, nullable=False)
    district = Column(String, nullable=False)
    commodity = Column(String, nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    stage_override = Column(Integer, nullable=True)
    stage_override_date = Column(Date, nullable=True)
    moisture = Column(Float, nullable=True)
    ph = Column(Float, nullable=True)
    N = Column(Float, nullable=True)
    P = Column(Float, nullable=True)
    K = Column(Float, nullable=True)
    sensor_timestamp = Column(DateTime, nullable=True)
    image_path = Column(Text, nullable=True)
    image_timestamp = Column(DateTime, nullable=True)

    logs = relationship("SensorImageLog", back_populates="farm")


class SensorImageLog(Base):
    __tablename__ = "sensor_image_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    farm_id = Column(String, ForeignKey("farms.farm_id"), nullable=False, index=True)
    run_type = Column(String, nullable=False)
    am_log_id = Column(Integer, ForeignKey("sensor_image_log.id"), nullable=True)
    logged_at = Column(DateTime, nullable=False)
    moisture = Column(Float, nullable=True)
    ph = Column(Float, nullable=True)
    N = Column(Float, nullable=True)
    P = Column(Float, nullable=True)
    K = Column(Float, nullable=True)
    sensor_timestamp = Column(DateTime, nullable=True)
    image_path = Column(Text, nullable=True)
    image_timestamp = Column(DateTime, nullable=True)
    computed_stage = Column(Integer, nullable=False)
    stage_source = Column(String, nullable=False)
    confidence_score = Column(Integer, nullable=True)
    advisory_json = Column(Text, nullable=True)
    diagnostic_json = Column(Text, nullable=True)
    next_cycle_flags = Column(Text, nullable=True)

    farm = relationship("Farm", back_populates="logs")
