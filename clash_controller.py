import datetime
import platform
import subprocess

now = datetime.datetime.now()
weekday = now.weekday()  # 0=Monday, 6=Sunday
hour = now.hour

python_cmd = "python3" if platform.system() != "Windows" else "python"

def run(script):
    print(f"Running {script}...")
    subprocess.run([python_cmd, f"_scripts/{script}"])

run("api_clan_tracker.py")
run("api_war_tracker.py")
run("api_raid_tracker.py")
run("war_player_tracker.py")
run("raid_player_tracker.py")