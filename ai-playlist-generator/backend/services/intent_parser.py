"""
Intent Parser Service
Extracts structured intent from a natural-language playlist request.
No external AI required — uses keyword and regex matching.
"""

import re
from typing import Optional

CURRENT_YEAR = 2024


def parse_intent(query: str) -> dict:
    q = query.lower()

    theme = _detect_theme(q)
    year_range = _detect_year_range(q)
    genres = _detect_genres(q)
    moods = _detect_moods(q, theme)
    count, one_per_year = _detect_count(q, year_range)

    return {
        "theme": theme,
        "year_range": year_range,
        "genres": genres,
        "moods": moods,
        "count": count,
        "one_per_year": one_per_year,
        "raw_query": query,
    }


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _detect_theme(q: str) -> str:
    theme_keywords = {
        "birthday":  ["birthday", "born", "birth", "bday", "celebrate my"],
        "party":     ["party", "celebration", "bash", "fiesta", "night out", "club"],
        "workout":   ["workout", "gym", "exercise", "run", "running", "cardio", "fitness", "pump up"],
        "study":     ["study", "focus", "concentration", "work from home", "coding", "reading"],
        "chill":     ["chill", "relax", "relaxing", "calm", "peaceful", "mellow", "lazy", "sleep", "unwind"],
        "road_trip": ["road trip", "driving", "drive", "travel", "long drive", "highway"],
        "romance":   ["romantic", "date night", "anniversary", "wedding", "love songs", "Valentine"],
        "sad":       ["sad", "heartbreak", "breakup", "cry", "melancholy", "down", "gloomy"],
        "morning":   ["morning", "wake up", "sunrise", "breakfast", "start the day"],
        "night":     ["night", "evening", "late night", "midnight", "after dark"],
    }
    for theme, keywords in theme_keywords.items():
        if any(kw in q for kw in keywords):
            return theme
    return "general"


def _detect_year_range(q: str) -> Optional[dict]:
    # "since YYYY" or "from YYYY"
    m = re.search(r'\b(?:since|from)\s+(\d{4})\b', q)
    if m:
        start = int(m.group(1))
        return {"start": max(start, 1970), "end": CURRENT_YEAR}

    # "YYYY to YYYY" or "YYYY - YYYY"
    m = re.search(r'\b(\d{4})\s*(?:to|-|through|until)\s*(\d{4})\b', q)
    if m:
        return {"start": int(m.group(1)), "end": int(m.group(2))}

    # "the 80s / 90s / 2000s / 2010s / 2020s"
    decade_map = {
        "80s": (1980, 1989), "1980s": (1980, 1989),
        "90s": (1990, 1999), "1990s": (1990, 1999),
        "2000s": (2000, 2009), "00s": (2000, 2009),
        "2010s": (2010, 2019), "10s": (2010, 2019),
        "2020s": (2020, CURRENT_YEAR),
    }
    for label, (start, end) in decade_map.items():
        if label in q:
            return {"start": start, "end": min(end, CURRENT_YEAR)}

    # bare 4-digit year
    m = re.search(r'\b(19[7-9]\d|20[0-2]\d)\b', q)
    if m:
        yr = int(m.group(1))
        return {"start": yr, "end": yr}

    return None


def _detect_genres(q: str) -> list:
    genre_keywords = {
        "Pop":        ["pop"],
        "Rock":       ["rock"],
        "Hard Rock":  ["hard rock"],
        "Hip-Hop":    ["hip-hop", "hip hop", "rap", "hiphop"],
        "R&B":        ["r&b", "rnb", "soul", "rhythm and blues"],
        "Country":    ["country"],
        "Dance":      ["dance", "edm", "electronic", "techno", "house"],
        "Alternative":["indie", "alternative", "alt rock"],
        "Grunge":     ["grunge"],
        "Jazz":       ["jazz"],
        "Classical":  ["classical"],
        "Latin":      ["latin", "reggaeton", "salsa"],
    }
    found = []
    for genre, keywords in genre_keywords.items():
        if any(kw in q for kw in keywords):
            found.append(genre)
    return found


def _detect_moods(q: str, theme: str) -> list:
    mood_keywords = {
        "happy":     ["happy", "upbeat", "fun", "joyful", "cheerful", "feel good", "positive", "good vibes"],
        "sad":       ["sad", "melancholy", "heartbreak", "breakup", "cry", "miss", "gloomy"],
        "energetic": ["energetic", "pump up", "intense", "hype", "power", "fast", "high energy"],
        "chill":     ["chill", "relax", "calm", "mellow", "ambient", "slow", "peaceful"],
        "romantic":  ["romantic", "love", "tender", "intimate", "sweet"],
    }
    # inherit from theme
    theme_mood_map = {
        "birthday":  "happy",
        "party":     "energetic",
        "workout":   "energetic",
        "study":     "chill",
        "chill":     "chill",
        "road_trip": "happy",
        "romance":   "romantic",
        "sad":       "sad",
        "morning":   "happy",
        "night":     "chill",
    }
    found = []
    for mood, keywords in mood_keywords.items():
        if any(kw in q for kw in keywords):
            found.append(mood)
    if not found and theme in theme_mood_map:
        found.append(theme_mood_map[theme])
    return found if found else ["general"]


def _detect_count(q: str, year_range: Optional[dict]) -> tuple:
    one_per_year = "every year" in q or "each year" in q or "one per year" in q or "one from each year" in q

    m = re.search(r'\b(\d+)\s+songs?\b', q)
    if m:
        return min(int(m.group(1)), 50), one_per_year

    if one_per_year and year_range:
        span = year_range["end"] - year_range["start"] + 1
        return min(span, 50), True

    return 20, one_per_year
