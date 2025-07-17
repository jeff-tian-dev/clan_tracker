import requests
import json
from datetime import datetime
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

# === API request to get clan members ===
url = f'https://api.clashofclans.com/v1/clans/{encoded_tag}/members'
response = requests.get(url, headers=headers)

if response.status_code != 200:
    print(f"❌ Failed to fetch clan data: {response.status_code}")
    exit()

data = response.json()
members = data.get('items', [])
clan_trophies = data.get('clan', {}).get('clanPoints', 0)  # fallback if not present

# === Prepare output folder ===
log_dir = Path("clan_logs")
log_dir.mkdir(exist_ok=True)

today_str = datetime.today().strftime('%Y-%m-%d')

# === Build list of player stats and calculate total trophies
player_stats = []
total_trophies = 0

for member in members:
    trophies = member.get('trophies', 0)
    total_trophies += trophies

    player_stats.append({
        'name': member.get('name'),
        'tag': member.get('tag'),
        'position': member.get('clanRank'),
        'trophies': trophies
    })

# === Wrap in metadata container
output = {
    "date": today_str,
    "totalPlayerTrophies": total_trophies,
    "members": player_stats
}

# === Save to file
stats_file = log_dir / f"clan_members.json"
with open(stats_file, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2)

print(f"✅ Player stats saved to {stats_file}")
