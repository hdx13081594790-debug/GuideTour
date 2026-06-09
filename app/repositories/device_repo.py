from datetime import UTC, datetime
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.device import Device
from app.schemas.location import LocationUpdateRequest

# DeviceRepository 负责 device 表。
#
# 数据流：
# /location/update -> DeviceRepository.update_location()
# -> 保存设备最后一次位置、朝向、姿态和 last_seen_at。
# 它补充 RedisLocationStore：Redis 负责实时，数据库负责可查询状态。


class DeviceRepository:
    def __init__(self, db: Session):
        self.db = db

    def update_location(self, payload: LocationUpdateRequest) -> Device:
        # 有 device_code 则更新；没有则创建。
        # MVP 中 payload.device_id 直接作为设备唯一编码。
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
        device.last_seen_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(device)
        return device
