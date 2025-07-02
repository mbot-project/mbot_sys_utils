# MBot System Utilities ROS2 Jazzy
Install scripts and utilities for setting up an MBot ROS2 environment.

This has been tested with Ubuntu 24 on the Raspberry Pi 5.

## Setting up a fresh image

### Install system dependencies

### Setup ROS2 Jazzy


### Set udev rules
```bash
cd ~/mbot_sys_utils/ros2_mbot_sys_utils/udev_rules
chmod +x ros-mbot.rules
./ros-mbot.rules 
```

### Install services
```bash
cd ~/mbot_sys_utils/ros2_mbot_sys_utils/services
./install_mbot_ros_services.sh 
```