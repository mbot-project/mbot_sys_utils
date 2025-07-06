#!/bin/bash

set -e  # Quit on error.

#### Install software from apt-get ####
sudo apt update
sudo apt upgrade -y

# Install Deps
sudo apt -y install gh colcon wget cmake gpg apt-transport-https minicom gcc-arm-none-eabi build-essential pkg-config libusb-1.0-0-dev
sudo apt -y install python3-dev python3-numpy python3-matplotlib python3-opencv python3-scipy python3-pip
sudo apt -y install python3-qrcode python3-luma.oled

# Install gpio pin control
sudo apt install gpiod -y

# Install firmware upload script
chmod +x mbot-upload-firmware
sudo cp mbot-upload-firmware /usr/local/bin

# Install pico-sdk
git clone --recurse-submodules https://github.com/raspberrypi/pico-sdk.git $HOME/pico-sdk

# Configure environment
export PICO_SDK_PATH=$HOME/pico-sdk
echo "export PICO_SDK_PATH=$HOME/pico-sdk" >> ~/.bashrc
source ~/.bashrc

# Install picotool
cd ~
wget https://github.com/raspberrypi/picotool/archive/refs/tags/2.1.1.zip
unzip 2.1.1.zip
cd picotool-2.1.1

mkdir build
cd build
cmake ..
make
sudo make install

# cleanup
cd ../..
rm 2.1.1.zip
rm -rf picotool-2.1.1
