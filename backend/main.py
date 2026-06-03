"""FastAPI server that exposes TRIBE v2 engagement analysis over HTTP."""

from __future__ import annotations

import tempfile
import uuid
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .tribe_engine import EngagementResult, TribeEngine

ALLOWED_EXTENSIONS = {".mp4", ".mov", ".webm", ".mkv", ".avi"}
MAX_UPLOAD_BYTES = 500 * 1024 * 1024

app = FastAPI(title="TRIBE v2 Video Engagement API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_engine: TribeEngine | None = None


def get_engine() -> TribeEngine:
    global _engine
    if _engine is None:
        _engine = TribeEngine()
    return _engine


@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": _engine is not None}


@app.post("/predict")
async def predict(video: UploadFile = File(...)) -> dict:
    suffix = Path(video.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Unsupported file type: {suffix}")

    tmp_dir = Path(tempfile.gettempdir()) / "tribev2_uploads"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    tmp_path = tmp_dir / f"{uuid.uuid4().hex}{suffix}"

    size = 0
    with tmp_path.open("wb") as f:
        while chunk := await video.read(1024 * 1024):
            size += len(chunk)
            if size > MAX_UPLOAD_BYTES:
                tmp_path.unlink(missing_ok=True)
                raise HTTPException(413, "File too large (max 500 MB)")
            f.write(chunk)

    try:
        result: EngagementResult = get_engine().analyze(tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)

    return {
        "score": result.score,
        "curve": result.curve,
        "peak_seconds": result.peak_seconds,
        "duration_s": result.duration_s,
        "n_vertices": result.n_vertices,
    }


FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/")
    def index():
        return FileResponse(FRONTEND_DIR / "index.html")
