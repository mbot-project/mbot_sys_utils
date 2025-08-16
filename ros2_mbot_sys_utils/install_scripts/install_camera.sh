#!/bin/bash

# This file is based on https://www.raspberrypi.com/documentation/computers/camera_software.html#building-libcamera

set -e  # Quit on error.

sudo apt update && sudo apt upgrade -y

# Install libcamera
echo "Installing libcamera dependencies..."
sudo apt install -y libboost-dev
sudo apt install -y libgnutls28-dev openssl libtiff5-dev pybind11-dev
sudo apt install -y qtbase5-dev libqt5core5a libqt5gui5 libqt5widgets5
sudo apt install -y meson cmake
sudo apt install -y python3-yaml python3-ply
sudo apt install -y libglib2.0-dev libgstreamer-plugins-base1.0-dev
sudo apt -y install python3-colcon-meson # for camera_ros

echo "Cloning libcamera..."
cd ~
git clone https://github.com/raspberrypi/libcamera.git
cd libcamera
meson setup build --buildtype=release -Dpipelines=rpi/vc4,rpi/pisp -Dipas=rpi/vc4,rpi/pisp -Dv4l2=true -Dgstreamer=enabled -Dtest=false -Dlc-compliance=disabled -Dcam=disabled -Dqcam=disabled -Ddocumentation=disabled -Dpycamera=enabled

echo "Building libcamera..."
ninja -C build

echo "Installing libcamera..."
sudo ninja -C build install

echo "Cleaning up..."
cd ~
rm -rf libcamera

# Install rpicam-apps
# This is a collection of apps that use libcamera same as libcamera-apps
echo "--------------------------------"
echo "Installing dependencies for rpicam-apps..."
sudo apt install -y cmake libboost-program-options-dev libdrm-dev libexif-dev
sudo apt install -y meson ninja-build
sudo apt-get install -y libepoxy-dev

echo "Cloning rpicam-apps..."
cd ~
git clone https://github.com/raspberrypi/rpicam-apps.git
cd rpicam-apps
meson setup build -Denable_libav=enabled -Denable_drm=enabled -Denable_egl=enabled -Denable_qt=enabled -Denable_opencv=disabled -Denable_tflite=disabled -Denable_hailo=disabled

echo "Building rpicam-apps..."
meson compile -C build

echo "Installing rpicam-apps..."
sudo meson install -C build

# update the cache
sudo ldconfig

echo "Cleaning up..."
cd ~
rm -rf rpicam-apps

# Install camera ROS2 packages
echo "--------------------------------"
echo "Installing camera ROS2 packages..."

sudo apt install -y ros-jazzy-image-transport
sudo apt install -y ros-jazzy-image-transport-plugins
sudo apt install -y ros-jazzy-image-pipeline
sudo apt install -y ros-jazzy-apriltag-ros