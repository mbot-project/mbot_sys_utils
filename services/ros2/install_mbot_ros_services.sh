#!/bin/bash

set -e  # Quit on error.

# Copy the scripts we need for the services.
sudo cp mbot_ros_oled_display.py /usr/local/etc/
sudo chmod +x /usr/local/etc/mbot_ros_oled_display.py

# Copy the services.
sudo cp mbot-oled.service /etc/systemd/system/mbot-oled.service

# Enable time sync wait service
sudo systemctl enable --now systemd-time-wait-sync.service

# Enable the services.
sudo systemctl daemon-reload
sudo systemctl enable mbot-oled.service

# Success message.
echo
echo "Installed and enabled the OLED display service."
