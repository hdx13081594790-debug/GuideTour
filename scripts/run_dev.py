import uvicorn

# 本地开发启动脚本。
#
# 等价于命令：
# python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
#
# 你现在也可以直接运行 app/main.py 或 VSCode launch.json。

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
