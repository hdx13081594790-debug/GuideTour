import logging

# 日志配置入口。
#
# main.py 在创建 FastAPI 应用前调用 configure_logging()。
# 后续服务层、httpx、uvicorn 输出的日志会使用统一格式，
# 便于在终端中追踪“请求 -> 服务 -> 外部 API”的调用过程。


def configure_logging() -> None:
    # MVP 阶段只做基础 INFO 日志。生产环境可以在这里扩展为
    # JSON 日志、请求 trace_id、文件日志或接入日志平台。
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
