"""
Planner Service
Translates parsed intent into an ordered list of concrete retrieval tasks.
"""


def create_plan(intent: dict) -> dict:
    tasks = []

    if intent.get("year_range"):
        yr = intent["year_range"]
        tasks.append({
            "task": "filter_by_year_range",
            "params": yr,
            "description": f"Filter catalog to years {yr['start']}–{yr['end']}",
        })

    if intent.get("genres"):
        tasks.append({
            "task": "filter_by_genre",
            "params": {"genres": intent["genres"]},
            "description": f"Filter by genre(s): {', '.join(intent['genres'])}",
        })

    moods = [m for m in intent.get("moods", []) if m != "general"]
    if moods:
        tasks.append({
            "task": "filter_by_mood",
            "params": {"moods": moods},
            "description": f"Filter by mood: {', '.join(moods)}",
        })

    if intent.get("one_per_year"):
        tasks.append({
            "task": "select_one_per_year",
            "params": {},
            "description": "Select one representative track per year",
        })
    else:
        n = intent.get("count", 20)
        tasks.append({
            "task": "select_top_n",
            "params": {"count": n},
            "description": f"Select top {n} tracks",
        })

    tasks.append({
        "task": "sort_chronologically",
        "params": {},
        "description": "Sort tracks chronologically by year then title",
    })

    tasks.append({
        "task": "generate_metadata",
        "params": {},
        "description": "Generate playlist name, description, and stats",
    })

    strategy = _choose_strategy(intent)

    return {
        "tasks": tasks,
        "strategy": strategy,
        "estimated_tracks": intent.get("count", 20),
    }


def _choose_strategy(intent: dict) -> str:
    if intent.get("one_per_year"):
        return "one_per_year_chronological"
    if intent.get("year_range"):
        return "year_range_filtered"
    if intent.get("genres"):
        return "genre_curated"
    if intent.get("moods") and intent["moods"] != ["general"]:
        return "mood_curated"
    return "general_top_n"
