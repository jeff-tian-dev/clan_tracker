#!/bin/bash

cd /home/ubuntu/clan_tracker

# Load .env (optional if you're not using it in shell)
export $(grep -v '^#' .env | xargs)

# Run controller
/usr/bin/python3 _scripts/controller.py

# Commit any changes
git add *.json
git commit -m "Auto update: $(date)" || echo "Nothing to commit"

# Push to GitHub
git push
