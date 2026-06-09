import pytest
from fastapi.testclient import TestClient
from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.main import app
from scripts.seed_poi import seed

# 测试公共夹具。
#
# 所有测试通过 client fixture 访问 FastAPI 应用，不需要真的启动 uvicorn。
# setup 阶段会 init_db + seed，保证 POI 和基础表存在。


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    init_db()
    seed()


@pytest.fixture
def client():
    return TestClient(app)
