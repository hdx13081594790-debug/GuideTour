from app.models.base import Base
import app.models  # noqa: F401
from app.core.config import get_settings
from app.db.session import engine


def init_db() -> None:
    if not get_settings().auto_create_tables:
        return
    Base.metadata.create_all(bind=engine)
