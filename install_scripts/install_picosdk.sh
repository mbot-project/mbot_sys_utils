#!/bin/bash

set -e  # Quit on error.

#### Install pico tools ####
mkdir -p Installers
cd Installers
wget https://raw.githubusercontent.com/raspberrypi/pico-setup/master/pico_setup.sh
chmod +x pico_setup.sh
./pico_setup.sh
