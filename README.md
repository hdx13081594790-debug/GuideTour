# 颐和园智慧导览 MVP Demo

一个可本地运行的“Web 后台 + 手机 H5 游客端”智慧导览 demo，覆盖语言自动识别、POI 路线推荐、智能互动问答、目标识别讲解四个核心功能。

## 快速启动

```powershell
python -m uvicorn app.main:app --reload --port 8000
```

打开：

- 游客端：http://127.0.0.1:8000
- 后台：http://127.0.0.1:8000/admin
- API 文档：http://127.0.0.1:8000/docs

## 技术说明

- 后端：FastAPI + Pydantic。
- 数据：默认使用标准库 SQLite，首次启动自动写入 10 个颐和园 POI、路线边和知识库。
- 缓存：提供内存缓存占位，后续可替换 Redis。
- Agent：用服务层模拟 LangGraph 的“识别语言 -> 判断意图 -> 调工具 -> 同语言回答”流程。
- 云端模型：ASR、LLM、VLM 当前为本地 demo fallback，API 响应结构已按云端模型接入预留。

## API

- `GET /api/poi`
- `POST /api/asr`
- `POST /api/chat`
- `POST /api/route/recommend`
- `POST /api/vision/recognize`
- `PUT /api/admin/poi/{poi_id}`

## 测试

```powershell
python -m unittest discover -s tests
```
