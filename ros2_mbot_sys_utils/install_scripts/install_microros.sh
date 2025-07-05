#!/bin/bash

set -e  # Quit on error.

echo "export PICO_TOOLCHAIN_PATH=/usr/bin/" >> ~/.bashrc
source ~/.bashrc

# Source the ROS 2 installation
source /opt/ros/$ROS_DISTRO/setup.bash

# install utilities
sudo apt install -y python3-rosdep

# Update dependencies using rosdep
sudo apt update 
sudo rosdep init && rosdep update

# Create a workspace and download the micro-ROS tools
cd ~
mkdir microros_ws
cd microros_ws
git clone -b $ROS_DISTRO https://github.com/micro-ROS/micro_ros_setup.git src/micro_ros_setup

rosdep install --from-paths src --ignore-src -y

# Build micro-ROS tools and source them
colcon build
source install/local_setup.bash

# Build microROS Agent
ros2 run micro_ros_setup create_agent_ws.sh
ros2 run micro_ros_setup build_agent.sh

source install/local_setup.sh

echo "source $PWD/install/local_setup.sh" >> ~/.bashrc