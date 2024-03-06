#!/bin/bash
# instructions from https://www.electronicshub.org/programming-raspberry-pi-pico-with-swd
mkdir -p Installers
cd Installers
sudo apt install automake autoconf build-essential texinfo libtool libftdi-dev libusb-1.0-0-dev gdb-multiarch
git clone https://github.com/raspberrypi/openocd.git --recursive --branch rp2040 --depth=1
cd openocd
./bootstrap
./configure --enable-ftdi --enable-sysfsgpio --enable-bcm2835gpio
make -j3
sudo make install
sudo apt-get install gdb-multiarch