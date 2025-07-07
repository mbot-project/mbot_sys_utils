#!/bin/bash

set -e  # Quit on error.

export PICO_TOOLCHAIN_PATH=/usr/bin/
echo "export PICO_TOOLCHAIN_PATH=/usr/bin/" >> ~/.bashrc

# install utilities
sudo apt install -y python3-rosdep

# Update dependencies using rosdep
sudo apt update
if [ ! -f /etc/ros/rosdep/sources.list.d/20-default.list ]; then
    sudo rosdep init
fi
rosdep update

# Create a workspace and download the micro-ROS tools
cd ~
mkdir microros_ws
cd microros_ws
git clone -b jazzy https://github.com/micro-ROS/micro_ros_setup.git src/micro_ros_setup

rosdep install --from-paths src --ignore-src -y

# Build micro-ROS tools and source them
colcon build
source install/local_setup.bash

# Build microROS Agent
ros2 run micro_ros_setup create_agent_ws.sh
ros2 run micro_ros_setup build_agent.sh

source install/local_setup.sh

echo "source $PWD/install/local_setup.sh" >> ~/.bashrc