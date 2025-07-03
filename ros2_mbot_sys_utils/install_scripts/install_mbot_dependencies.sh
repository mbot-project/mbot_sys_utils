#!/bin/bash

set -e  # Quit on error.

#### Install software from apt-get ####
sudo apt update
sudo apt upgrade -y

# Install gpio pin control
sudo apt install gpiod -y

# Install firmware upload script
sudo cp mbot-upload-firmware /usr/local/bin
