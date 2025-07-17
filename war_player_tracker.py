import json
import os
from datetime import datetime

# Directory and file constants
WAR_LOGS_DIR = "war_logs"
CLAN_STATS_FILE = os.path.join("clan_logs", "clan_members.json")
OUTPUT_FILE = os.path.join(WAR_LOGS_DIR, "player_stats_war.json")


def load_latest_war():
    """Return (data, date) for the newest war log."""
    if not os.path.isdir(WAR_LOGS_DIR):
        return None, None
    files = [f for f in os.listdir(WAR_LOGS_DIR)
             if f.startswith("war_") and f.endswith(".json")]
    if not files:
        return None, None
    files.sort(reverse=True)
    latest = files[0]
    path = os.path.join(WAR_LOGS_DIR, latest)
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    # filename format: war_YYYYMMDD_*.json
    parts = latest.split("_")
    date = parts[1]
    return data, date


def load_existing_stats():
    """Load existing player stats or return empty dict."""
    if not os.path.isfile(OUTPUT_FILE):
        return {}
    with open(OUTPUT_FILE, encoding="utf-8") as f:
        return json.load(f)


def load_clan_members():
    """Load current clan members from JSON file."""
    if not os.path.isfile(CLAN_STATS_FILE):
        return []
    with open(CLAN_STATS_FILE, encoding="utf-8") as f:
        return json.load(f).get("members", [])


def fill_missing_dates(stats, dates, placeholder_factory):
    """
    Ensure each player has an entry for every date in dates.
    placeholder_factory(date, tag) → dict
    """
    for tag, record in stats.items():
        if tag == "timestamp":
            continue
        existing = {entry["date"] for entry in record.get("history", [])}
        for d in dates:
            if d not in existing:
                record["history"].append(placeholder_factory(d, tag))
        record["history"].sort(key=lambda x: x["date"])
    return stats


def war_placeholder(date, tag, max_attacks):
    """Default placeholder for missing war entries (not in war)."""
    return {
        "date": date,
        "attacksUsed": "---",
        "starsEarned": "---",
        "destruction": "---",
        "attacksMissed": 0,
        "zeroParticipation": True
    }


def main():
    # Load latest war log
    war_data, date = load_latest_war()
    if war_data is None:
        print("No war logs found.")
        return

    # Prepare stats and members
    stats = load_existing_stats()
    members = load_clan_members()

    # Ensure every current clan member has a stats record
    for m in members:
        tag = m.get("Tag") or m.get("tag")
        name = m.get("Name") or m.get("name")
        stats.setdefault(tag, {"name": name, "tag": tag, "history": []})

    # Determine max attacks per member
    max_attacks = war_data.get("attacksPerMember", 0)

    # Update stats with this war's entries
    for member in war_data.get("clan", {}).get("members", []):
        tag = member.get("tag")
        # Ensure record exists if a new participant appears
        stats.setdefault(tag, {"name": member.get("name", ""), "tag": tag, "history": []})

        attacks = member.get("attacks", [])
        used = len(attacks)
        stars = sum(a.get("stars", 0) for a in attacks)
        destruction = sum(a.get("destructionPercentage", 0) for a in attacks)
        missed = max_attacks - used

        entry = {
            "date": date,
            "attacksUsed": used,
            "starsEarned": stars,
            "destruction": destruction,
            "attacksMissed": missed,
            "zeroParticipation": (used == 0)
        }

        history = stats[tag]["history"]
        if history and history[-1]["date"] == date:
            history[-1] = entry
        else:
            history.append(entry)

    # Fill placeholders for members who weren't in the war
    stats = fill_missing_dates(stats, [date], lambda d, t: war_placeholder(d, t, max_attacks))

    # Save results
    stats["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    os.makedirs(WAR_LOGS_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()