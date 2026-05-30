# 颐和园 AI 导览项目 MVP

这是一个 Python + FastAPI 后端 MVP，用于演示“路线导览、即时景点讲解、眼镜画面理解与手势交互”的最小闭环。

## 已实现能力

- POI 查询：`/api/v1/poi/search`、`/api/v1/poi/nearby`、`/api/v1/poi/{poi_id}`
- 路线导览：`/api/v1/navigation/route`、`/api/v1/navigation/nearest`、`/api/v1/navigation/update-position`、`/api/v1/navigation/stop`、`/api/v1/navigation/{task_id}/state`
- Agent 对话：`/api/v1/agent/chat`
- 附近景点讲解：`/api/v1/agent/explain-nearby`
- RAG 抽象与 Mock：`/api/v1/rag/retrieve`、`/api/v1/rag/answer`
- 视觉与手势 Mock：`/api/v1/vision/analyze-frame`、`/api/v1/vision/analyze-frames`、`/api/v1/vision/gesture`
- 拍照记录：`/api/v1/photo/capture`、`/api/v1/photo/session/{session_id}`
- 百度地图服务端 Provider：地点检索、步行路线规划、逆地理编码，失败时自动回落到本地园区路线
- WebSocket 实时推送：`/api/v1/ws/{session_id}`
- 手机端演示客户端：`/client`

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

手机端演示客户端：

```text
http://127.0.0.1:8000/client
```

默认使用 SQLite：`summer_palace_guide.db`。如需切换 MySQL、Redis，可复制 `.env.example` 并修改配置。实时位置状态和导航状态会优先写入 Redis，Redis 不可用时自动回退到进程内存，方便本地开发。

Redis key 示例：

```text
guide:session:{session_id}:context
guide:device:{device_id}:location
guide:navigation:{task_id}:state
guide:session:{session_id}:active_navigation
```

如果本机有 `redis-cli`，可以这样验证：

```cmd
redis-cli GET guide:session:s001:context
redis-cli GET guide:session:s001:active_navigation
```

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

## 数据库迁移

项目已接入 Alembic。当前本地开发默认 `AUTO_CREATE_TABLES=true`，启动服务时仍会自动建表，方便快速调试。多人协作、MySQL 或部署环境建议改为：

```env
AUTO_CREATE_TABLES=false
```

然后使用迁移命令建表：

```powershell
python -m alembic upgrade head
python -m scripts.seed_poi
```

以后如果修改了 `app/models/` 里的表结构，生成迁移：

```powershell
python -m alembic revision --autogenerate -m "describe schema change"
```

检查生成的 `alembic/versions/` 文件无误后，再执行：

```powershell
python -m alembic upgrade head
```

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

读取导航状态：

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/navigation/{task_id}/state
Invoke-RestMethod http://127.0.0.1:8000/api/v1/navigation/session/s001/active-state
```

导航位置更新现在会自动处理：

- 到达判断：距离目的地小于 25 米返回 `status=arrived`
- step 推进：根据剩余距离推进 `current_step_index`
- 偏航判断：距离路线 polyline 超过 30 米先累计偏航次数，连续 3 次才返回 `off_route=true`
- Redis 同步：每次更新都会刷新 `guide:navigation:{task_id}:state`

## WebSocket 实时推送

眼镜端或调试端连接：

```text
ws://127.0.0.1:8000/api/v1/ws/{session_id}
```

连接成功后会收到：

```json
{"type":"connected","session_id":"s001"}
```

当前会推送这些事件：

| 事件 | 触发来源 |
| --- | --- |
| `location_updated` | `POST /api/v1/location/update` |
| `navigation_started` | `POST /api/v1/navigation/route`、`POST /api/v1/navigation/nearest` |
| `navigation_updated` | `POST /api/v1/navigation/update-position` |
| `navigation_stopped` | `POST /api/v1/navigation/stop` |
| `vision_analyzed` | `POST /api/v1/vision/analyze-frame`、`POST /api/v1/vision/analyze-frames` |
| `gesture_detected` | `POST /api/v1/vision/gesture` |

## 架构说明

地图服务通过 `MapProviderClient` 抽象，已提供 `AmapClient`、`BaiduClient`、`LocalGraphRouter`。业务层不直接依赖某个地图厂商。

内部坐标统一使用 `lng, lat`。高德适配输出 `lng,lat`，百度适配输出 `lat,lng`，转换函数位于 `app/services/map/coordinate.py`。

RAG、视觉模型和手势识别均已留出可替换接口，当前使用 mock 实现，后续接入公司向量库或真实模型时可优先替换服务层。
