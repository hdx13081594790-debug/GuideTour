from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# 统一异常处理。
#
# 服务层如果发现业务错误，不直接返回 Response，而是 raise AppError。
# main.py 启动时调用 register_exception_handlers(app)，把 AppError 转成
# 前端能稳定解析的 JSON：{"detail": "..."}。
#
# 数据流：
# Service/Repository -> raise AppError -> FastAPI exception handler
# -> JSONResponse -> 前端 api.post/api.get 抛出 Error(data.detail)。


class AppError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code


def register_exception_handlers(app: FastAPI) -> None:
    # 注册一次即可。后续新增自定义异常，也可以在这里集中管理。
    @app.exception_handler(AppError)
    async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})
