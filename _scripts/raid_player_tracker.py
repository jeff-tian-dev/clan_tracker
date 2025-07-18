import json
import os
from pathlib import Path
from datetime import datetime

# Directory and file constants
RAID_LOGS_DIR = "../raid_logs"
CLAN_STATS_FILE = os.path.join("../clan_logs", "clan_members.json")
OUTPUT_FILE = os.path.join(RAID_LOGS_DIR, "player_stats_raid.json")


def load_latest_raid():
    """Return (data, date) for the newest raid log."""
    if not os.path.isdir(RAID_LOGS_DIR):
        return None, None
    files = [f for f in os.listdir(RAID_LOGS_DIR)
             if f.startswith("raid_") and f.endswith(".json")]
    if not files:
        return None, None
    files.sort(reverse=True)
    latest = files[0]
    path = os.path.join(RAID_LOGS_DIR, latest)
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    # extract date from filename: raid_YYYYMMDD.json
    date = latest.split("_")[1].split(".")[0]
    return data, date


def get_raid_dates():
    folder = Path('../raid_logs')
    dates = [
        p.stem.split('_')[1]
        for p in folder.iterdir()
        if p.is_file() and p.name.startswith('raid_') and p.suffix == '.json'
    ]
    return sorted(dates)


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


def fill_missing_dates(stats, dates, members, state):
    """
    Ensure each player has an entry for every date in dates.
    placeholder_factory(date, tag) → dict
    """
    tags = [member['tag'] for member in members]
    latest_date = dates[-1]
    for tag, info in stats.items():
        if tag == "timestamp":
            continue
        existing = {entry["date"] for entry in info["history"]}
        for d in dates:
            if d not in existing:
                if d == latest_date and tag in tags and state != "ended":
                    info["history"].append(ongoing_placeholder(d))
                else:
                    info["history"].append(raid_placeholder(d))
        info["history"].sort(key=lambda x: x["date"])
    return stats


def raid_placeholder(date):
    """Default placeholder after raid ended: unknown stats."""
    return {
        "date": date,
        "attacksUsed": "---",
        "capitalGold": "---",
        "avgLootPerAttack": "---",
        "attacksMissed": 0,
        "missedRaid": True
    }


def ongoing_placeholder(date):
    """Placeholder during ongoing raid: mark full missed attacks."""
    return {
        "date": date,
        "attacksUsed": 0,
        "capitalGold": 0,
        "avgLootPerAttack": "---",
        "attacksMissed": 6,
        "missedRaid": False
    }


def main():
    # Load data
    raid_data, date = load_latest_raid()
    if raid_data is None:
        print("No raid logs found.")
        return

    state = raid_data.get("state")  # 'ended' or other

    stats = load_existing_stats()
    members = load_clan_members()

    # Ensure stats entries for all current members
    for m in members:
        tag = m.get("tag")
        stats.setdefault(tag, {"name": m.get("name"), "tag": tag, "history": []})

    # Update stats with latest raid entries
    for member in raid_data.get("members", []):
        tag = member["tag"]
        stats.setdefault(tag, {"name": member.get("name"), "tag": tag, "history": []})
        # attacks is an integer in JSON, not a list
        attacks = member.get("attacks", 0)
        limit = member.get("attackLimit", 0) + member.get("bonusAttackLimit", 0)
        capital = member.get("capitalResourcesLooted", 0)
        avg_loot = round(capital / attacks, 1) if attacks else (0 if state != "ended" else "---")
        missed = (limit - attacks) if limit else None
        entry = {
            "date": date,
            "attacksUsed": attacks,
            "capitalGold": capital,
            "avgLootPerAttack": avg_loot,
            "attacksMissed": missed,
            "missedRaid": False
        }
        hist = stats[tag]["history"]
        if hist and hist[-1]["date"] == date:
            hist[-1] = entry
        else:
            hist.append(entry)

    # Fill placeholders: ongoing vs ended
    stats = fill_missing_dates(stats, get_raid_dates(), members, state)

    # Write back
    stats["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    os.makedirs(RAID_LOGS_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
