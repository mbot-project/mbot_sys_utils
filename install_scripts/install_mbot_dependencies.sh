#!/bin/bash

set -e  # Quit on error.

#### Install software from apt-get ####
apt update
apt upgrade -y
apt -y install ssh git software-properties-common apt-transport-https wget gpg cmake

# install dependencies !! Need to make this is complete and all are used
apt -y install build-essential wget dkms \
    autoconf automake autotools-dev gdb libglib2.0-dev libgtk2.0-dev \
    libusb-dev libusb-1.0-0-dev freeglut3-dev libboost-dev libatlas-base-dev \
    libgsl-dev libjpeg-dev default-jdk doxygen openssl libssl-dev libdc1394-dev \
    v4l-utils minicom gcc-arm-none-eabi libnewlib-arm-none-eabi

apt -y install mesa-common-dev libgl1-mesa-dev libglu1-mesa-dev

# install python3 and scipy
apt -y install python3-dev python3-numpy python3-matplotlib python3-opencv python3-scipy python3-pygame python3-pip

# Install python pkgs for MBot OLED
apt -y install python3-qrcode python3-luma.oled


# Clone pico-sdk
wget https://github.com/MBot-Project-Development/pico_sdk/archive/refs/tags/v1.0.0.zip
unzip v1.0.0.zip 

export PICO_SDK_PATH="$PWD/pico_sdk-1.0.0"

# install picotool
wget https://github.com/raspberrypi/picotool/archive/refs/tags/1.1.1.zip
unzip 1.1.1.zip
cd picotool-1.1.1
mkdir build && cd build
cmake ..
make
sudo make install
cd ../..

# remove picotool install files
rm 1.1.1.zip
rm -rf picotool-1.1.1

# remove pico-sdk
rm v1.0.0.zip
rm -rf pico_sdk-1.0.0

# Install firmware upload script
sudo cp mbot-upload-firmware /usr/local/bin

#### Enable features for specific platforms ####
# Check if running on RPi
if grep -q "Raspberry Pi" /proc/device-tree/model; then
    echo "RPi detected, installing raspi-config"
    apt -y install raspi-config libcamera-dev 
    raspi-config nonint do_vnc 0
    raspi-config nonint do_ssh 0
    raspi-config nonint do_camera 0
    raspi-config nonint do_i2c 0
fi

if grep -q "NVIDIA Jetson Nano" /proc/device-tree/model; then
    echo "Jetson Nano detected"
fi

echo "Done Installing!"
