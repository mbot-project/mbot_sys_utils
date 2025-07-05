# MBot System Utilities ROS2 Jazzy
Install scripts and utilities for setting up an MBot ROS2 environment.

This has been tested with Ubuntu 24 on the Raspberry Pi 5.

## Setting up a fresh image
### 0. Get Ubuntu SD card ready
Flash Ubuntu 24 onto an SD card, then plug in a monitor, keyboard, and mouse to your Raspberry Pi, boot up, and set the desired configurations. The default login information should be:
* User: `mbot`
* Password: `i<3robots!`

**Note, the user name must be `mbot`.**

### 1. Install system dependencies
```bash
./install_mbot_dependencies.sh 
```
### 2. Setup ROS2 Jazzy
```bash
./install_ros2_jazzy.sh
./install_microros.sh
```
### 3. Copy mbot_config.txt
```bash
sudo cp mbot_config.txt /boot/firmware
```

### 4. Set udev rules
```bash
cd ~/mbot_sys_utils/ros2_mbot_sys_utils/udev_rules
chmod +x ros-mbot.rules
./ros-mbot.rules 
```

### 5. Install services
```bash
cd ~/mbot_sys_utils/ros2_mbot_sys_utils/services
./install_mbot_ros_services.sh 
```

### 6. Copy MWireless connect script
```bash
cd ~/mbot_sys_utils/ros2_mbot_sys_utils
cp SecureW2_JoinNow.run ~
```