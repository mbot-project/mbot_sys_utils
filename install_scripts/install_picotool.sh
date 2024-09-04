#!/bin/bash
echo "[Setup] Apt Installing required packages..."
sudo apt install cmake gcc-arm-none-eabi libnewlib-arm-none-eabi build-essential -y

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

echo "[Setup] Done!"
