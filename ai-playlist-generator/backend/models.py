"""
Pydantic models for request / response contracts.
"""

from pydantic import BaseModel
from typing import Any, Optional


class GenerateRequest(BaseModel):
    query: str


class WorkflowStep(BaseModel):
    step: int
    name: str
    status: str                  # "completed" | "failed"
    duration_ms: int
    output: dict[str, Any]


class Track(BaseModel):
    id: int
    title: str
    artist: str
    year: int
    genre: str
    mood: str
    energy: float
    bpm: int
    duration: str
    album: str


class Playlist(BaseModel):
    name: str
    description: str
    tracks: list[Track]
    total_tracks: int
    total_duration: str


class LogEntry(BaseModel):
    timestamp: str
    level: str
    service: str
    message: str
    data: Optional[dict[str, Any]] = None


class GenerateResponse(BaseModel):
    request_id: str
    query: str
    workflow: list[WorkflowStep]
    playlist: Playlist
    audit_log: list[LogEntry]
