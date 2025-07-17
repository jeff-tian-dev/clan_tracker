import requests
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()
API_TOKEN = os.getenv("COC_API_TOKEN")
CLAN_TAG = os.getenv("COC_CLAN_TAG")

encoded_tag = CLAN_TAG.replace("#", "%23")
headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Accept": "application/json"
}

# === Fetch current war ===
url = f"https://api.clashofclans.com/v1/clans/{encoded_tag}/currentwar"
response = requests.get(url, headers=headers)

if response.status_code != 200:
    print(f"❌ Failed to fetch war data: {response.status_code}")
    exit()

war_data = response.json()

# === Check state ===
if war_data.get("state") == "notInWar":
    print("⚠️ Clan is not currently in war.")
    exit()



# === Ensure war_logs folder exists ===
log_dir = Path("war_logs")
log_dir.mkdir(exist_ok=True)

# === Load or create manifest ===
manifest_path = log_dir / "manifest.json"
manifest = []
if manifest_path.exists():
    with open(manifest_path) as f:
        manifest = json.load(f)

# === Extract war metadata ===
end_time = war_data.get("endTime", "")
end_date = end_time.split("T")[0].replace("-", "") if end_time else datetime.utcnow().strftime("%Y%m%d")

opponent_name_raw = war_data.get("opponent", {}).get("name", "Unknown")
opponent_name_clean = opponent_name_raw.replace(" ", "_").replace("/", "_")
filename = f"war_{end_date}_{opponent_name_clean}.json"
war_path = log_dir / filename

# === Save war JSON file ===
with open(war_path, "w", encoding="utf-8") as f:
    json.dump(war_data, f, indent=2)
print(f"✅ Saved current war to {filename}")

# === Extract stats for manifest ===
clan = war_data.get("clan", {})
opponent = war_data.get("opponent", {})

clan_stars = clan.get("stars", 0)
opponent_stars = opponent.get("stars", 0)
clan_destruction = round(clan.get("destructionPercentage", 0.0), 3)
opponent_destruction = round(opponent.get("destructionPercentage", 0.0), 3)
clan_attacks = clan.get("attacks", 0)
opponent_attacks = opponent.get("attacks", 0)

# === Determine result ===
if clan_stars > opponent_stars:
    result = "win"
elif clan_stars < opponent_stars:
    result = "lose"
else:
    result = "tie"


# === Build manifest entry ===
summary = {
    "file": filename,
    "date": end_date,
    "opponent": opponent_name_raw,
    "result": result,
    "teamSize": war_data.get("teamSize", 0),
    "clanStars": clan_stars,
    "clanDestruction": clan_destruction,
    "clanAttacks": clan_attacks,
    "opponentStars": opponent_stars,
    "opponentDestruction": opponent_destruction,
    "opponentAttacks": opponent_attacks
}

# === Prevent duplicates by date ===
manifest = [entry for entry in manifest if entry["date"] != end_date]
manifest.insert(0, summary)

# === Save updated manifest ===
with open(manifest_path, "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2)
print("📄 Updated war manifest.")
