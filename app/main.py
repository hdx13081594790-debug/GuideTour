from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app import repository
from app.database import init_db
from app.models import (
    AsrResponse,
    ChatRequest,
    ChatResponse,
    POI,
    POIInput,
    RouteRequest,
    RouteResponse,
    VisionResponse,
)
from app.services.agent import run_guide_agent
from app.services.language import detect_language
from app.services.route import recommend_route
from app.services.vision import recognize_image

app = FastAPI(title="颐和园智慧导览 MVP", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    init_db()


app.mount("/static", StaticFiles(directory="app/static"), name="static")


def _parse_multipart(content_type: str, body: bytes) -> tuple[dict[str, str], dict[str, tuple[str, bytes]]]:
    marker = "boundary="
    if marker not in content_type:
        return {}, {}
    boundary = content_type.split(marker, 1)[1].strip().strip('"')
    boundary_bytes = f"--{boundary}".encode()
    fields: dict[str, str] = {}
    files: dict[str, tuple[str, bytes]] = {}

    for raw_part in body.split(boundary_bytes):
        part = raw_part.strip(b"\r\n")
        if not part or part == b"--" or b"\r\n\r\n" not in part:
            continue
        raw_headers, data = part.split(b"\r\n\r\n", 1)
        headers = raw_headers.decode("utf-8", errors="ignore")
        disposition = next((line for line in headers.split("\r\n") if line.lower().startswith("content-disposition")), "")
        attrs: dict[str, str] = {}
        for section in disposition.split(";"):
            if "=" in section:
                key, value = section.strip().split("=", 1)
                attrs[key] = value.strip().strip('"')
        name = attrs.get("name")
        if not name:
            continue
        data = data.rstrip(b"\r\n")
        if "filename" in attrs:
            files[name] = (attrs.get("filename") or "upload.bin", data)
        else:
            fields[name] = data.decode("utf-8", errors="ignore")
    return fields, files


async def _read_upload(request: Request, default_filename: str = "upload.bin") -> tuple[str, bytes, dict[str, str]]:
    body = await request.body()
    content_type = request.headers.get("content-type", "")
    fields, files = _parse_multipart(content_type, body)
    if files:
        filename, content = next(iter(files.values()))
        return filename, content, fields
    return default_filename, body, fields


@app.get("/")
def tourist_app() -> FileResponse:
    return FileResponse("app/static/index.html")


@app.get("/admin")
def admin_app() -> FileResponse:
    return FileResponse("app/static/admin.html")


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "mode": "local-demo"}


@app.get("/api/poi", response_model=list[POI])
def api_list_poi() -> list[dict]:
    return repository.list_pois()


@app.put("/api/admin/poi/{poi_id}", response_model=POI)
def api_upsert_poi(poi_id: str, payload: POIInput) -> dict:
    if poi_id != payload.id:
        raise HTTPException(status_code=400, detail="URL 中的 POI id 必须和请求体一致。")
    return repository.upsert_poi(payload.model_dump())


@app.get("/api/admin/knowledge")
def api_knowledge() -> list[dict]:
    return repository.list_docs()


@app.post("/api/asr", response_model=AsrResponse)
async def api_asr(request: Request) -> dict:
    filename, data, _ = await _read_upload(request, "audio.bin")
    filename_language = detect_language(filename)
    transcript = ""
    try:
        transcript = data[:2000].decode("utf-8").strip()
    except UnicodeDecodeError:
        transcript = ""
    if not transcript:
        transcript = "请介绍一下佛香阁，并推荐下一站。"
    language = detect_language(transcript) if transcript else filename_language
    return {
        "language": language,
        "transcript": transcript,
        "confidence": 0.62 if transcript else 0.4,
        "note": "本地 demo 未配置云端 ASR，已使用文件名/文本内容模拟识别。接入云端 ASR 后保持响应结构不变。",
    }


@app.post("/api/chat", response_model=ChatResponse)
def api_chat(payload: ChatRequest) -> dict:
    return run_guide_agent(
        session_id=payload.session_id,
        message=payload.message,
        language=payload.language,
        current_poi_id=payload.current_poi_id,
    )


@app.post("/api/route/recommend", response_model=RouteResponse)
def api_route(payload: RouteRequest) -> dict:
    try:
        return recommend_route(
            start_poi_id=payload.start_poi_id,
            end_poi_id=payload.end_poi_id,
            duration_minutes=payload.duration_minutes,
            interests=payload.interests,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/vision/recognize", response_model=VisionResponse)
async def api_vision_recognize(request: Request) -> dict:
    filename, content, fields = await _read_upload(request, "image.jpg")
    language = fields.get("language", "zh")
    current_poi_id = fields.get("current_poi_id") or None
    return recognize_image(filename, content, language=language, current_poi_id=current_poi_id)
