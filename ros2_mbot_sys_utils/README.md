# MBot System Utilities ROS2 Jazzy
Install scripts and utilities for setting up an MBot ROS2 environment.

This has been tested with Ubuntu 24 on the Raspberry Pi 5.

## Setting up a fresh image
1. Git clone [mbot_sys_utils](https://github.com/mbot-project/mbot_sys_utils)
2. `cd ~/mbot_sys_utils/ros2_mbot_sys_utils/install_scripts`
3. Run `./install_mbot_dependencies.sh`
4. Install ROS2 Jazzy `./install_ros2_jazzy.sh`
5. Install microROS
    ```bash
    source ~/.bashrc
    ./install_microros.sh
    ```
    This output is fine:
    ```bash
    --- stderr: micro_ros_agent                                          
    Cloning into 'xrceagent'...
    HEAD is now at 7362281 Release v2.4.3
    Cloning into 'spdlog'...
    HEAD is now at eb322062 Bump version to 1.9.2
    ---
    Finished <<< micro_ros_agent [2min 27s]

    Summary: 2 packages finished [2min 40s]
      1 package had stderr output: micro_ros_agent
    ```
5. Install Camera
    ```bash
    ./install_camera.sh
    ```
## System Config
1. Copy mbot_config.txt
```bash
cd ~/mbot_sys_utils/ros2_mbot_sys_utils
sudo cp mbot_config.txt /boot/firmware
```
2. Set udev rules
```bash
cd ~/mbot_sys_utils/ros2_mbot_sys_utils/udev_rules
./install_rules.sh 
```
3. Install services
```bash
cd ~/mbot_sys_utils/ros2_mbot_sys_utils/services
./install_mbot_ros_services.sh 
```
4. Download the latest SecureW2 script to the home directory from this [link](https://cloud.securew2.com/public/92472/UMich-WiFi/).