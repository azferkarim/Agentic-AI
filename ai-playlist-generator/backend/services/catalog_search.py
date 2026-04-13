"""
Catalog Search Service
Loads the local songs.json and applies filters derived from the planner tasks.
"""

import json
import os
from typing import Optional

_CATALOG_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "songs.json")
_catalog: Optional[list] = None


def load_catalog() -> list:
    global _catalog
    if _catalog is None:
        with open(_CATALOG_PATH, "r", encoding="utf-8") as f:
            _catalog = json.load(f)
    return _catalog


def search(intent: dict, plan: dict) -> dict:
    songs = list(load_catalog())          # shallow copy so we never mutate the cache
    original_count = len(songs)
    filters_applied: list[str] = []

    # --- year range ---
    yr = intent.get("year_range")
    if yr:
        songs = [s for s in songs if yr["start"] <= s["year"] <= yr["end"]]
        filters_applied.append(f"year: {yr['start']}–{yr['end']}")

    # --- genre ---
    genres = [g.lower() for g in intent.get("genres", [])]
    if genres:
        genre_filtered = [
            s for s in songs
            if any(g in s["genre"].lower() for g in genres)
        ]
        if genre_filtered:
            songs = genre_filtered
            filters_applied.append(f"genre: {', '.join(intent['genres'])}")

    # --- mood ---
    moods = [m for m in intent.get("moods", []) if m != "general"]
    if moods:
        mood_filtered = [s for s in songs if s.get("mood", "").lower() in moods]
        if mood_filtered:
            songs = mood_filtered
            filters_applied.append(f"mood: {', '.join(moods)}")

    return {
        "songs": songs,
        "total_searched": original_count,
        "total_matched": len(songs),
        "filters_applied": filters_applied,
    }
