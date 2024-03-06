#!/bin/bash

set -e  # Quit on error.

sudo cp 50-mbot.rules /etc/udev/rules.d/
sudo cp 99-wifi-dongle.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
sudo udevadm trigger
