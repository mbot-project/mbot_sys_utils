#!/bin/bash

set -e  # Quit on error.

# Get latest ARMv8 nomachine .deb (For both Jetson Nano and RPi4; see https://kb.nomachine.com/AR02R01074)
wget https://www.nomachine.com/free/arm/v8/deb -O nomachine.deb
sudo dpkg -i nomachine.deb

# Clean up.
rm nomachine.deb

echo "Done installing NoMachine."
