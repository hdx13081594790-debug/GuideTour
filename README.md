# 颐和园智慧导览
# 颐和园 AI 导览项目 MVP

这是一个 Python + FastAPI 后端 MVP，用于演示“路线导览、即时景点讲解、眼镜画面理解与手势交互”的最小闭环。

## 已实现能力

- POI 查询：`/api/v1/poi/search`、`/api/v1/poi/nearby`、`/api/v1/poi/{poi_id}`
- 路线导览：`/api/v1/navigation/route`、`/api/v1/navigation/nearest`、`/api/v1/navigation/update-position`、`/api/v1/navigation/stop`
- Agent 对话：`/api/v1/agent/chat`
- 附近景点讲解：`/api/v1/agent/explain-nearby`
- RAG 抽象与 Mock：`/api/v1/rag/retrieve`、`/api/v1/rag/answer`
- 视觉与手势 Mock：`/api/v1/vision/analyze-frame`、`/api/v1/vision/analyze-frames`、`/api/v1/vision/gesture`
- 拍照记录：`/api/v1/photo/capture`、`/api/v1/photo/session/{session_id}`

## 本地启动

```powershell
venv\Scripts\python -m pip install -r requirements.txt
venv\Scripts\python -m scripts.seed_poi
venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

健康检查：

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

默认使用 SQLite：`summer_palace_guide.db`。如需切换 MySQL、Redis，可复制 `.env.example` 并修改配置。当前 MVP 保留 Redis 配置位，实时位置先使用进程内存存储。

## 初始化数据

```powershell
venv\Scripts\python -m scripts.seed_poi
```

Seed 包含德和园、德和园大戏楼、仁寿门、仁寿殿、苏州街、谐趣园、长廊、佛香阁、昆明湖、排云殿、厕所、医疗室、游客服务中心、入口、出口等 POI。

## 测试

```powershell
venv\Scripts\python -m pytest -q
```

## 示例请求

最近厕所导航：

PowerShell：

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/navigation/nearest -Method Post -ContentType 'application/json' -Body '{"session_id":"s001","origin":{"lng":116.2699,"lat":39.9991},"target_type":"toilet","radius_meters":1000}'
```

cmd.exe：

```cmd
curl -X POST http://127.0.0.1:8000/api/v1/navigation/nearest -H "Content-Type: application/json" -d "{\"session_id\":\"s001\",\"origin\":{\"lng\":116.2699,\"lat\":39.9991},\"target_type\":\"toilet\",\"radius_meters\":1000}"
```

对话触发导航：

PowerShell：

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/agent/chat -Method Post -ContentType 'application/json' -Body '{"session_id":"s001","device_id":"glass001","text":"我想去最近的厕所","location":{"lng":116.2699,"lat":39.9991},"heading":85}'
```

cmd.exe：

```cmd
curl -X POST http://127.0.0.1:8000/api/v1/agent/chat -H "Content-Type: application/json" -d "{\"session_id\":\"s001\",\"device_id\":\"glass001\",\"text\":\"我想去最近的厕所\",\"location\":{\"lng\":116.2699,\"lat\":39.9991},\"heading\":85}"
```

附近讲解：

PowerShell：

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/agent/explain-nearby -Method Post -ContentType 'application/json' -Body '{"session_id":"s001","device_id":"glass001","location":{"lng":116.2728,"lat":39.99955},"heading":90,"accuracy_meters":5}'
```

cmd.exe：

```cmd
curl -X POST http://127.0.0.1:8000/api/v1/agent/explain-nearby -H "Content-Type: application/json" -d "{\"session_id\":\"s001\",\"device_id\":\"glass001\",\"location\":{\"lng\":116.2728,\"lat\":39.99955},\"heading\":90,\"accuracy_meters\":5}"
```

RAG 问答：

PowerShell：

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/rag/answer -Method Post -ContentType 'application/json' -Body '{"query":"这个建筑为什么有三层？","poi_id":2}'
```

cmd.exe：

```cmd
curl -X POST http://127.0.0.1:8000/api/v1/rag/answer -H "Content-Type: application/json" -d "{\"query\":\"这个建筑为什么有三层？\",\"poi_id\":2}"
```

手势 Mock：

PowerShell：

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/vision/analyze-frames -Method Post -ContentType 'application/json' -Body '{"session_id":"s001","device_id":"glass001","frame_ids":["f1"],"mock_gesture":"take_photo"}'
```

cmd.exe：

```cmd
curl -X POST http://127.0.0.1:8000/api/v1/vision/analyze-frames -H "Content-Type: application/json" -d "{\"session_id\":\"s001\",\"device_id\":\"glass001\",\"frame_ids\":[\"f1\"],\"mock_gesture\":\"take_photo\"}"
```

## 架构说明

地图服务通过 `MapProviderClient` 抽象，已提供 `AmapClient`、`BaiduClient`、`LocalGraphRouter`。没有真实地图 Key 时会使用本地园区路网 mock 返回可演示路线。

内部坐标统一使用 `lng, lat`。高德适配输出 `lng,lat`，百度适配输出 `lat,lng`，转换函数位于 `app/services/map/coordinate.py`。

RAG、视觉模型和手势识别均已留出可替换接口，当前使用 mock 实现，后续接入公司向量库或真实模型时可优先替换服务层。
