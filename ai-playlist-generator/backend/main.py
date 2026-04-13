"""
AI Playlist Generator — FastAPI backend
Run:  uvicorn main:app --reload --port 8000
"""

import time
import uuid

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from models import GenerateRequest, GenerateResponse, WorkflowStep, Playlist, Track, LogEntry
from services.intent_parser import parse_intent
from services.planner import create_plan
from services.catalog_search import search
from services.playlist_builder import build
from services.logger import AuditLogger

app = FastAPI(title="AI Playlist Generator", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the frontend from /
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.isdir(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/")
    def serve_index():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


@app.post("/api/generate-playlist", response_model=GenerateResponse)
def generate_playlist(req: GenerateRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query must not be empty.")

    request_id = str(uuid.uuid4())
    logger = AuditLogger()
    workflow: list[WorkflowStep] = []

    logger.info("api", f"Received request [{request_id}]: {req.query!r}")

    # -------------------------------------------------------------------------
    # Step 1 — Intent Understanding
    # -------------------------------------------------------------------------
    t0 = time.perf_counter()
    logger.info("intent_parser", f"Parsing natural-language query: {req.query!r}")
    intent = parse_intent(req.query)
    duration_ms = int((time.perf_counter() - t0) * 1000)

    logger.info("intent_parser", "Intent parsed successfully", {
        "theme": intent["theme"],
        "year_range": intent.get("year_range"),
        "moods": intent["moods"],
        "count": intent["count"],
        "one_per_year": intent["one_per_year"],
    })

    workflow.append(WorkflowStep(
        step=1,
        name="Intent Understanding",
        status="completed",
        duration_ms=max(duration_ms, 1),
        output={
            "theme": intent["theme"],
            "year_range": intent.get("year_range"),
            "genres": intent.get("genres", []),
            "moods": intent["moods"],
            "count": intent["count"],
            "one_per_year": intent["one_per_year"],
        },
    ))

    # -------------------------------------------------------------------------
    # Step 2 — Task Planning
    # -------------------------------------------------------------------------
    t0 = time.perf_counter()
    logger.info("planner", "Creating execution plan from intent")
    plan = create_plan(intent)
    duration_ms = int((time.perf_counter() - t0) * 1000)

    logger.info("planner", f"Plan ready — {len(plan['tasks'])} tasks, strategy: {plan['strategy']}")

    workflow.append(WorkflowStep(
        step=2,
        name="Task Planning",
        status="completed",
        duration_ms=max(duration_ms, 1),
        output={
            "strategy": plan["strategy"],
            "tasks": [t["description"] for t in plan["tasks"]],
            "estimated_tracks": plan["estimated_tracks"],
        },
    ))

    # -------------------------------------------------------------------------
    # Step 3 — Data Retrieval
    # -------------------------------------------------------------------------
    t0 = time.perf_counter()
    logger.info("catalog_search", "Searching local song catalog")
    search_results = search(intent, plan)
    duration_ms = int((time.perf_counter() - t0) * 1000)

    logger.info("catalog_search", (
        f"Search complete: {search_results['total_matched']} / "
        f"{search_results['total_searched']} songs matched"
    ), {"filters_applied": search_results["filters_applied"]})

    if not search_results["songs"]:
        logger.warning("catalog_search", "No songs matched — relaxing constraints")

    workflow.append(WorkflowStep(
        step=3,
        name="Data Retrieval",
        status="completed",
        duration_ms=max(duration_ms, 1),
        output={
            "catalog_size": search_results["total_searched"],
            "songs_matched": search_results["total_matched"],
            "filters_applied": search_results["filters_applied"],
        },
    ))

    # -------------------------------------------------------------------------
    # Step 4 — Playlist Assembly
    # -------------------------------------------------------------------------
    t0 = time.perf_counter()
    logger.info("playlist_builder", "Assembling final playlist")
    playlist_data = build(search_results, intent)
    duration_ms = int((time.perf_counter() - t0) * 1000)

    logger.info("playlist_builder", (
        f"Playlist '{playlist_data['name']}' built: "
        f"{playlist_data['total_tracks']} tracks, {playlist_data['total_duration']}"
    ))

    workflow.append(WorkflowStep(
        step=4,
        name="Playlist Assembly",
        status="completed",
        duration_ms=max(duration_ms, 1),
        output={
            "strategy": plan["strategy"],
            "songs_selected": playlist_data["total_tracks"],
            "total_duration": playlist_data["total_duration"],
        },
    ))

    # -------------------------------------------------------------------------
    # Step 5 — Final Output
    # -------------------------------------------------------------------------
    t0 = time.perf_counter()
    logger.info("output", f"Finalising response for request [{request_id}]")

    tracks = [Track(**t) for t in playlist_data["tracks"]]
    playlist = Playlist(
        name=playlist_data["name"],
        description=playlist_data["description"],
        tracks=tracks,
        total_tracks=playlist_data["total_tracks"],
        total_duration=playlist_data["total_duration"],
    )
    duration_ms = int((time.perf_counter() - t0) * 1000)

    logger.info("output", "Response ready", {
        "playlist_name": playlist.name,
        "track_count": playlist.total_tracks,
    })

    workflow.append(WorkflowStep(
        step=5,
        name="Final Output",
        status="completed",
        duration_ms=max(duration_ms, 1),
        output={
            "playlist_name": playlist.name,
            "total_tracks": playlist.total_tracks,
            "total_duration": playlist.total_duration,
            "request_id": request_id,
        },
    ))

    return GenerateResponse(
        request_id=request_id,
        query=req.query,
        workflow=workflow,
        playlist=playlist,
        audit_log=[LogEntry(**e) for e in logger.entries()],
    )


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "ai-playlist-generator"}
