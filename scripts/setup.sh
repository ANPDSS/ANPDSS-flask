#!/usr/bin/env bash

set -e  # exit immediately if any command fails

echo "Creating virtual environment..."
python3 -m venv venv

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing requirements..."
pip install -r requirements.txt

echo "Making scripts executable..."
chmod +x ./scripts/db_init.py
chmod +x ./scripts/init_friends_data.py

echo "Running database initialization..."
echo "y" | python ./scripts/db_init.py

echo "Initializing friends data..."
python ./scripts/init_friends_data.py

echo "Setup complete ✅"
