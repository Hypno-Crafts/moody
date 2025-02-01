#!/bin/bash

# Update and upgrade system packages
sudo apt update && sudo apt upgrade -y

# Install Python and virtual environment if not installed
sudo apt install -y python3 python3-venv python3-pip libgl1 python3-pyqt5

# Create and activate a virtual environment
python3 -m venv moodyvenv
source moodyvenv/bin/activate

# Install pip and upgrade it
pip install --upgrade pip

# Install packages from requirements.txt
pip install -r requirements.txt

sudo cp moody.service /etc/systemd/system/moody.service
sudo systemctl enable moody.service
sudo systemctl start moody.service
sudo systemctl status moody.service

echo "Setup finished."
