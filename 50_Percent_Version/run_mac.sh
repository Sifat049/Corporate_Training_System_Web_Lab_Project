#!/usr/bin/env bash
# macOS one-command setup + run.   Usage:  chmod +x run_mac.sh && ./run_mac.sh
# Banglish note: eta pura setup automatic kore - venv, pip install, migrate, demo data, server start.
set -e
cd "$(dirname "$0")/backend"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 not found. Install Python from https://www.python.org/downloads/ (or: brew install python)"
  exit 1
fi

if [ ! -d venv ]; then
  echo ">> Creating virtual environment..."
  python3 -m venv venv
fi
source venv/bin/activate

echo ">> Installing requirements..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

echo ">> Applying database migrations..."
python manage.py migrate

echo ">> Creating demo data (skipped if it already exists)..."
python manage.py seed_demo

echo ""
echo "=============================================================="
echo " Open http://127.0.0.1:8000/  (stop server with Ctrl + C)"
echo " admin / Admin@123   hr_manager / Hr@12345"
echo " trainer1 / Trainer@123   employee1 / Employee@123"
echo "=============================================================="
python manage.py runserver
