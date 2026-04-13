"""
Playlist Builder Service
Applies selection strategy and assembles the final playlist.
"""

import random

PLAYLIST_NAMES = {
    "birthday":  "Birthday Hits",
    "party":     "Party Anthems",
    "workout":   "Workout Bangers",
    "study":     "Study Vibes",
    "chill":     "Chill Session",
    "road_trip": "Road Trip Classics",
    "romance":   "Love Songs",
    "sad":       "Feels Playlist",
    "morning":   "Morning Boost",
    "night":     "Late Night Vibes",
    "general":   "AI Mix",
}

PLAYLIST_DESCRIPTIONS = {
    "birthday":  "A celebratory journey through the best hits — one from every year just for you.",
    "party":     "High-energy anthems to keep the party going all night long.",
    "workout":   "Power-packed tracks to fuel your next session.",
    "study":     "Smooth, distraction-free music to help you focus and get things done.",
    "chill":     "Laid-back sounds for when you just need to unwind.",
    "road_trip": "The perfect soundtrack for miles of open road.",
    "romance":   "Tender, heartfelt songs for that special someone.",
    "sad":       "Sometimes you just need to feel all the feelings.",
    "morning":   "Bright and cheerful tracks to start your day right.",
    "night":     "Late-night vibes for quiet hours and city lights.",
    "general":   "A curated mix assembled just for your request.",
}


def build(search_results: dict, intent: dict) -> dict:
    songs = search_results["songs"]
    theme = intent.get("theme", "general")
    yr = intent.get("year_range")
    count = intent.get("count", 20)

    # --- selection strategy ---
    if intent.get("one_per_year") and yr:
        selected = _one_per_year(songs, yr["start"], yr["end"])
    else:
        selected = _top_n(songs, count)

    # sort chronologically, then alphabetically within same year
    selected = sorted(selected, key=lambda s: (s["year"], s["title"]))

    # --- metadata ---
    base_name = PLAYLIST_NAMES.get(theme, "AI Mix")
    if yr and yr["start"] != yr["end"]:
        playlist_name = f"{base_name} ({yr['start']}–{yr['end']})"
    elif yr:
        playlist_name = f"{base_name} ({yr['start']})"
    else:
        playlist_name = base_name

    description = PLAYLIST_DESCRIPTIONS.get(theme, PLAYLIST_DESCRIPTIONS["general"])
    total_seconds = sum(s.get("duration_seconds", 210) for s in selected)
    duration_str = _format_duration(total_seconds)

    return {
        "name": playlist_name,
        "description": description,
        "tracks": selected,
        "total_tracks": len(selected),
        "total_duration": duration_str,
    }


# ---------------------------------------------------------------------------
# selection helpers
# ---------------------------------------------------------------------------

def _one_per_year(songs: list, start: int, end: int) -> list:
    """Pick the best-scoring track for each year in the range."""
    by_year: dict[int, list] = {}
    for s in songs:
        by_year.setdefault(s["year"], []).append(s)

    result = []
    for year in range(start, end + 1):
        candidates = by_year.get(year)
        if candidates:
            # prefer high energy, break ties randomly
            candidates_sorted = sorted(candidates, key=lambda x: x.get("energy", 0), reverse=True)
            result.append(candidates_sorted[0])
    return result


def _top_n(songs: list, n: int) -> list:
    """Return up to n tracks, ordered by energy descending, with a small random shuffle for variety."""
    sorted_songs = sorted(songs, key=lambda x: x.get("energy", 0), reverse=True)
    pool = sorted_songs[:max(n * 2, 10)]   # over-select then sample
    random.shuffle(pool)
    return pool[:n]


def _format_duration(total_seconds: int) -> str:
    h = total_seconds // 3600
    m = (total_seconds % 3600) // 60
    s = total_seconds % 60
    if h > 0:
        return f"{h}h {m}m"
    return f"{m}m {s}s"
