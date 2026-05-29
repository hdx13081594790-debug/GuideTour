from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.device import Device
from app.schemas.location import LocationUpdateRequest


class DeviceRepository:
    def __init__(self, db: Session):
        self.db = db

    def update_location(self, payload: LocationUpdateRequest) -> Device:
        device = self.db.execute(select(Device).where(Device.device_code == payload.device_id)).scalar_one_or_none()
        if not device:
            device = Device(device_code=payload.device_id, user_session_id=payload.session_id)
            self.db.add(device)
        device.user_session_id = payload.session_id
        device.last_longitude = payload.location.lng
        device.last_latitude = payload.location.lat
        device.last_heading = payload.heading
        device.last_pitch = payload.pitch
        device.last_roll = payload.roll
        device.last_seen_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(device)
        return device
