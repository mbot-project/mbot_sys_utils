#!/bin/bash

echo "This script assumes you have a stable wifi connection (aka starting at 'Install Updates' in the setup instructions)."
echo "It assumes you have mbot_workspace with this repo cloned."
echo "It also assumes you have a set up, passwordless SSH key for git."
echo "Preferably, connect to MWireless before this since there's a lot of cloning"
set -e

if [ -z "$1" ]; then
    echo "Please provide the bot's hostname (with no quotes) as an argument."
    exit 1
fi

MBOT_HOSTNAME_LINE="mbot_hostname=$1"

# Install Updates section
echo "[SETUP] installing updates"
sudo apt -y update
sudo apt -y upgrade
# Start SSH (pending testing)
sudo systemctl enable ssh
sudo systemctl start ssh

# Additional config
sudo cp ./rpi_config.txt /boot/config.txt

#not setting desktop colors :(

cd ..
# Clone packages
echo "[SETUP] cloning repos"
repos=("mbot_lcm_base" "mbot_firmware" "mbot_autonomy" "mbot_gui" "mbot_web_app" "rplidar_lcm_driver")

eval "$(ssh-agent -s)"
ssh-add /home/mbot/.ssh/id_ed25519

# clone the repo if the folder not exists
for repo in "${repos[@]}"; do
    [ ! -d "/home/mbot/mbot_workspace/$repo" ] && git clone "git@github.com:MBot-Project-Development/$repo.git"
done

# sys utils setup
echo "[SETUP] setup for sys_utils"
cd /home/mbot/mbot_workspace/mbot_sys_utils
sudo ./install_scripts/install_mbot_dependencies.sh
./install_scripts/install_lcm.sh
sudo ./install_scripts/install_nomachine.sh
#Replacing hostname in mbot_config.txt
sed -i "1s/.*/$MBOT_HOSTNAME_LINE/" mbot_config.txt
sudo cp ./mbot_config.txt /boot
cd ./udev_rules
./install_rules.sh
cd ../services
./install_mbot_services.sh

# Setting up other repos
# mbot_lcm_base
cd /home/mbot/mbot_workspace/mbot_lcm_base
echo "[SETUP] setup for lcm_base"
git checkout v0.1 && git pull
[ -d "./build" ] && sudo rm -rf build
mkdir build && cd build
cmake ..
make
sudo make install
echo "[SETUP] finished setup for lcm_base"

# rplidar_lcm_driver
cd /home/mbot/mbot_workspace/rplidar_lcm_driver
echo "[SETUP] setup for rplidar_lcm_driver"
git pull && git submodule update --init --recursive
[ -d "./build" ] && sudo rm -rf build
mkdir build && cd build
cmake ..
make
sudo make install
cd ../services
./install_rplidar_service.sh
echo "[SETUP] finished setup for rplidar_lcm_driver"

# mbot_web_app
cd /home/mbot/mbot_workspace/mbot_web_app
echo "[SETUP] setup for web_app"
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.3/install.sh | bash
source ~/.bashrc #get nvm without launching new window by sourcing bashrc again
nvm install 18
./scripts/install_nginx.sh
./scripts/install_app.sh
echo "[SETUP] finished setup for web_app"

# mbot_firmware
cd /home/mbot/mbot_workspace/mbot_firmware
echo "[SETUP] setup for firmware"
git checkout main && git pull
sudo ./setup.sh

# Installation from readme file
sudo apt-get install libftdi-dev gdb-multiarch
git clone https://github.com/raspberrypi/openocd.git --recursive --branch rp2040 --depth=1
cd openocd
./bootstrap
./configure --enable-ftdi --enable-sysfsgpio --enable-bcm2835gpio
make -j4
sudo make install
cd ..

# Build firmware, but don't upload (not sure if SWD is connected)
[ -d "./build" ] && sudo rm -rf build
mkdir build && cd build
cmake ..
make
echo "[SETUP] finished setup for firmware"

# mbot_autonomy
cd /home/mbot/mbot_workspace/mbot_autonomy
echo "[SETUP] setup for autonomy"
git checkout main && git pull
sudo ./scripts/install.sh
echo "[SETUP] finished setup for autonomy"

# Reboot to set up everything
echo "[SETUP FINISHED] rebooting."
sudo reboot
