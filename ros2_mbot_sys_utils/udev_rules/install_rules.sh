#!/bin/bash

set -e  # Quit on error.

# Copy udev rules
sudo cp ros-mbot.rules /etc/udev/rules.d/99-ros-mbot.rules
sudo udevadm control --reload-rules
sudo udevadm trigger

# Add current user to the 'video' group (for camera access without sudo)
sudo usermod -aG video "$USER"

echo
echo "✅ User '$USER' has been added to the 'video' group."
echo "   You need to log out and log back in (or reboot) for the change to take effect."
