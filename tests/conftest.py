import pytest
from fastapi.testclient import TestClient
from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.main import app
from scripts.seed_poi import seed


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    init_db()
    seed()


@pytest.fixture
def client():
    return TestClient(app)
