#!/bin/bash

set -e  # Quit on error.

# Copy udev rules
sudo cp ros-mbot.rules /etc/udev/rules.d/99-ros-mbot.rules
sudo udevadm control --reload-rules
sudo udevadm trigger

echo "✅ MBot USB CDC rules installed."
echo "   /dev/mbot_debug  -> Debug/printf console"
echo "   /dev/mbot_microros    -> MicroROS communication"
echo "   Verify with: ls -l /dev/mbot_*"

# Add current user to the 'video' group (for camera access without sudo)
sudo usermod -aG video "$USER"

echo
echo "✅ User '$USER' has been added to the 'video' group."
echo "   You need to reboot for the change to take effect."
echo

