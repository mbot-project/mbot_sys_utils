#!/bin/bash

set -e  # Quit on error.

# Toolchain path
export PICO_TOOLCHAIN_PATH=/usr/bin/
grep -qxF 'export PICO_TOOLCHAIN_PATH=/usr/bin/' ~/.bashrc || echo 'export PICO_TOOLCHAIN_PATH=/usr/bin/' >> ~/.bashrc

# install utilities
sudo apt-get update
sudo apt-get install -y --no-install-recommends python3-rosdep

# Update dependencies using rosdep
if [ ! -f /etc/ros/rosdep/sources.list.d/20-default.list ]; then
    sudo rosdep init
fi
rosdep update

# Create a workspace and download the micro-ROS tools
MICROROS_WS=$HOME/microros_ws
mkdir -p "$MICROROS_WS/src"
cd "$MICROROS_WS"
if [ ! -d src/micro_ros_setup ]; then
    git clone -b jazzy https://github.com/micro-ROS/micro_ros_setup.git src/micro_ros_setup
fi

rosdep install --from-paths src --ignore-src -y

# Build micro-ROS tools and source them
colcon build
source install/local_setup.bash

# Build microROS Agent
ros2 run micro_ros_setup create_agent_ws.sh
ros2 run micro_ros_setup build_agent.sh

source install/local_setup.sh

grep -qxF "source $MICROROS_WS/install/local_setup.sh" ~/.bashrc || echo "source $MICROROS_WS/install/local_setup.sh" >> ~/.bashrc