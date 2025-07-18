import requests
import json
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()
API_TOKEN = os.getenv("COC_API_TOKEN")
CLAN_TAG = os.getenv("COC_CLAN_TAG")

encoded_tag = CLAN_TAG.replace('#', '%23')
headers = {
    'Authorization': f'Bearer {API_TOKEN}',
    'Accept': 'application/json'
}

# === Fetch Capital Raid Seasons ===
url = f"https://api.clashofclans.com/v1/clans/{encoded_tag}/capitalraidseasons"
response = requests.get(url, headers=headers)

if response.status_code != 200:
    print(f"❌ Failed to fetch raid data: {response.status_code}")
    exit()

raid_data = response.json()
entries = raid_data.get('items', [])

# === Ensure raid_logs folder exists ===
log_dir = Path("../raid_logs")
log_dir.mkdir(exist_ok=True)

# === Load or create manifest ===
manifest_path = log_dir / "manifest.json"
manifest = []
if manifest_path.exists():
    with open(manifest_path) as f:
        manifest = json.load(f)

# === Only save the most recent raid ===
if entries:
    latest = entries[0]
    end_date = latest['endTime'].split('T')[0].replace('-', '')  # Format: YYYYMMDD
    filename = f"raid_{end_date}.json"
    raid_path = log_dir / filename

    with open(raid_path, 'w') as f:
        json.dump(latest, f, indent=2)
    print(f"✅ Saved latest raid to {filename}")

    total_attacks = latest.get("totalAttacks", 0)
    enemy_districts_destroyed = latest.get("enemyDistrictsDestroyed", 0)
    attacks_per_district = (
        round(total_attacks / enemy_districts_destroyed, 2)
        if enemy_districts_destroyed > 0 else 0.0
    )

    summary = {
        "file": filename,
        "date": end_date,
        "totalAttacks": total_attacks,
        "attacksPerDistrict": attacks_per_district,
        "enemyDistrictsDestroyed": enemy_districts_destroyed,
        "offensiveReward": latest.get("offensiveReward", 0),
        "defensiveReward": latest.get("defensiveReward", 0),
        "participants": len(latest.get("members", []))
    }

    # Replace if already exists
    manifest = [e for e in manifest if e['date'] != end_date]
    manifest.insert(0, summary)

    # === Save updated manifest ===
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    print(f"📄 Updated raid manifest.")
else:
    print("⚠️ No raid entries found.")
