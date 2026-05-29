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
- 百度地图服务端 Provider：地点检索、步行路线规划、逆地理编码，失败时自动回落到本地园区路线

## 本地启动

```powershell
python -m pip install -r requirements.txt
python -m scripts.seed_poi
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

健康检查：

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

默认使用 SQLite：`summer_palace_guide.db`。如需切换 MySQL、Redis，可复制 `.env.example` 并修改配置。当前 MVP 保留 Redis 配置位，实时位置先使用进程内存存储。

## 启用百度地图服务端 API

复制 `.env.example` 为 `.env`，然后设置：

```env
MAP_PROVIDER=baidu
BAIDU_AK=你的百度地图服务端AK
```

不要把真实 AK 写入 README、`.env.example` 或提交记录中。`.env` 已经被 `.gitignore` 忽略，适合保存本机密钥。

当前 `BaiduClient` 使用这些百度 Web 服务能力：

- 地点检索：搜索外部 POI 或补充本地 POI 数据
- 步行路线规划：计算步行距离、耗时、分步导航和路线点
- 逆地理编码：把当前位置转换为地址或区域描述

园区内部路线仍保留 `LocalGraphRouter` 兜底。百度 API 无法返回园内细路、请求失败、AK 缺失或配额受限时，系统会继续返回可演示的本地路线。

## 初始化数据

```powershell
python -m scripts.seed_poi
```

Seed 包含德和园、德和园大戏楼、仁寿门、仁寿殿、苏州街、谐趣园、长廊、佛香阁、昆明湖、排云殿、厕所、医疗室、游客服务中心、入口、出口等 POI。

## 测试

```powershell
python -m pytest -q
```

## 示例请求

最近厕所导航：

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/navigation/nearest -Method Post -ContentType 'application/json; charset=utf-8' -Body '{"session_id":"s001","origin":{"lng":116.2699,"lat":39.9991},"target_type":"toilet","radius_meters":1000}'
```

对话触发导航：

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/agent/chat -Method Post -ContentType 'application/json; charset=utf-8' -Body '{"session_id":"s001","device_id":"glass001","text":"我想去最近的厕所","location":{"lng":116.2699,"lat":39.9991},"heading":85}'
```

附近讲解：

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/agent/explain-nearby -Method Post -ContentType 'application/json; charset=utf-8' -Body '{"session_id":"s001","device_id":"glass001","location":{"lng":116.2728,"lat":39.99955},"heading":90,"accuracy_meters":5}'
```

RAG 问答：

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/rag/answer -Method Post -ContentType 'application/json; charset=utf-8' -Body '{"query":"这个建筑为什么有三层？","poi_id":2}'
```

手势 Mock：

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/vision/analyze-frames -Method Post -ContentType 'application/json; charset=utf-8' -Body '{"session_id":"s001","device_id":"glass001","frame_ids":["f1"],"mock_gesture":"take_photo"}'
```

## 架构说明

地图服务通过 `MapProviderClient` 抽象，已提供 `AmapClient`、`BaiduClient`、`LocalGraphRouter`。业务层不直接依赖某个地图厂商。

内部坐标统一使用 `lng, lat`。高德适配输出 `lng,lat`，百度适配输出 `lat,lng`，转换函数位于 `app/services/map/coordinate.py`。

RAG、视觉模型和手势识别均已留出可替换接口，当前使用 mock 实现，后续接入公司向量库或真实模型时可优先替换服务层。
