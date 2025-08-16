#!/bin/bash

set -e  # Quit on error.

#### Install software from apt-get ####
sudo apt-get update
sudo apt-get upgrade -y

# Install dependencies
sudo apt-get install -y  \
    gh wget cmake gpg apt-transport-https minicom gcc-arm-none-eabi \
    autoconf automake autotools-dev libglib2.0-dev libnewlib-arm-none-eabi \
    libstdc++-arm-none-eabi-newlib libusb-dev freeglut3-dev libboost-dev libatlas-base-dev \
    libgsl-dev libjpeg-dev openssl libssl-dev v4l-utils \
    mesa-common-dev libgl1-mesa-dev libglu1-mesa-dev \
    build-essential pkg-config libusb-1.0-0-dev \
    python3-dev python3-numpy python3-matplotlib python3-opencv python3-scipy python3-pip \
    python3-qrcode python3-luma.oled \
    gpiod 
    
# Install firmware upload script
sudo install -m 755 mbot-upload-firmware /usr/local/bin/mbot-upload-firmware

# Install pico-sdk
if [ -d "$HOME/pico-sdk" ]; then
    git -C "$HOME/pico-sdk" pull --recurse-submodules
else
    git clone --depth 1 --recurse-submodules https://github.com/raspberrypi/pico-sdk.git "$HOME/pico-sdk"
fi

# Configure environment
export PICO_SDK_PATH="$HOME/pico-sdk"
grep -qxF "export PICO_SDK_PATH=$HOME/pico-sdk" ~/.bashrc || echo "export PICO_SDK_PATH=$HOME/pico-sdk" >> ~/.bashrc

# Install picotool
PICOTOOL_VERSION=2.2.0
rm -f /tmp/picotool-${PICOTOOL_VERSION}.zip
rm -rf /tmp/picotool-${PICOTOOL_VERSION}
wget -q https://github.com/raspberrypi/picotool/archive/refs/tags/${PICOTOOL_VERSION}.zip -O /tmp/picotool-${PICOTOOL_VERSION}.zip
cd /tmp
unzip -q picotool-${PICOTOOL_VERSION}.zip
cd picotool-${PICOTOOL_VERSION}

mkdir build
cd build
cmake .. -DPICO_SDK_PATH="$PICO_SDK_PATH"
make -j$(nproc)
sudo make install

# cleanup
cd /
rm -rf /tmp/picotool-${PICOTOOL_VERSION} /tmp/picotool-${PICOTOOL_VERSION}.zip

# Final apt cleanup
sudo apt-get autoremove -y
sudo apt-get autoclean
sudo apt-get clean
