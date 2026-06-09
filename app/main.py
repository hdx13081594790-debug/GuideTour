from contextlib import asynccontextmanager
import sys
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

# app/main.py 是整个后端的入口文件：
# 1. 创建 FastAPI 应用；
# 2. 初始化数据库和种子 POI；
# 3. 挂载前端静态文件；
# 4. 注册所有 /api/v1/... 路由。
#
# 数据流大致是：
# 浏览器/眼镜端 -> FastAPI 路由层(app/api/v1/routes)
# -> 服务层(app/services) -> Repository/外部 API/Redis/数据库
# -> Pydantic 响应模型 -> 前端展示。

# 当你在 VSCode 里直接运行 app/main.py 时，Python 默认只把 app/
# 目录当成导入搜索路径。这里把项目根目录 GuideTour 加入 sys.path，
# 这样 from app.xxx import ... 才能找到顶层 app 包。
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import uvicorn

from app.api.v1.routes import agent, config, location, navigation, photo, poi, rag, vision, ws
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.db.init_db import init_db
from app.schemas.common import HealthResponse
from scripts.seed_poi import seed


configure_logging()
settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    # 应用启动时执行一次：
    # init_db() 创建 SQLAlchemy 表；
    # seed() 写入 MVP 演示所需的颐和园 POI。
    # 注意：真正生产环境通常会用 Alembic 迁移和后台数据导入，
    # 不会每次启动都 seed。
    init_db()
    seed()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
register_exception_handlers(app)
static_dir = Path(__file__).resolve().parent / "static"

# 前端不是 npm/Vite 单独启动，而是普通 HTML/CSS/JS 静态文件。
# /static/client/app.js、/static/client/styles.css 都由 FastAPI 直接提供。
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse()


@app.get("/client", include_in_schema=False)
def mobile_client() -> FileResponse:
    # 手机端演示页面入口。浏览器访问 /client 时返回 index.html，
    # index.html 再加载 /static/client/app.js 和 styles.css。
    return FileResponse(static_dir / "client" / "index.html")


# 所有业务 API 都统一挂在 settings.api_prefix，默认是 /api/v1。
app.include_router(agent.router, prefix=settings.api_prefix)
app.include_router(config.router, prefix=settings.api_prefix)
app.include_router(location.router, prefix=settings.api_prefix)
app.include_router(navigation.router, prefix=settings.api_prefix)
app.include_router(photo.router, prefix=settings.api_prefix)
app.include_router(poi.router, prefix=settings.api_prefix)
app.include_router(rag.router, prefix=settings.api_prefix)
app.include_router(vision.router, prefix=settings.api_prefix)
app.include_router(ws.router, prefix=settings.api_prefix)

# 允许 VSCode 直接运行 app/main.py。正常部署时更推荐：
# python -m uvicorn app.main:app --host 127.0.0.1 --port 8010 --reload
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8010,
        reload=True
    )
