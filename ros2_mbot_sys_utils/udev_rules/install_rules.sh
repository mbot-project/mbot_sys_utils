#!/bin/bash

set -e  # Quit on error.

sudo cp ros-mbot.rules /etc/udev/rules.d/99-ros-mbot.rules
sudo udevadm control --reload-rules
sudo udevadm trigger
