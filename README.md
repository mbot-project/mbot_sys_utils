# mbot_sys_utils
Install scripts and utilities for setting up MBot environment on Ubuntu/Debian

### Setting up a fresh image ###
1. Install dependencies using scripts in install_scripts directory.
    ```bash
    sudo ./install_scripts/install_mbot_dependencies.sh
    ./install_scripts/install_lcm.sh
    ```

2. Optional installs:
    ```bash
    sudo ./install_scripts/install_nomachine.sh   # Recommended for debugging.
    sudo ./install_scripts/install_vscode.sh      # Only if you want to develop on the Pi.
    ```

3. Copy `mbot_config.txt` to the proper loacation in the boot folder.
    - First check your OS release: `cat /etc/os-release`
    - On Ubuntu 22.04 and Raspberry Pi OS 12 (**Bookworm**), the proper loacation is `/boot/firmware`. Run the following:
        ```bash
        sudo cp mbot_config.txt /boot/firmware
        ```
    - On Raspberry Pi OS prior to Bookworm, such as 11 (bullseye), this is just `/boot`:
        ```bash
        sudo cp mbot_config.txt /boot
        ```

4. Edit the configuration:
    ```bash
    sudo nano [/boot/mbot_config.txt, /boot/firmware/mbot_config.txt]
    ```

5. Install udev rules:
    ```bash
    cd udev_rules
    ./install_rules.sh
    ```

6. Install services:
    ```bash
    cd services
    ./install_mbot_services.sh
    ```

7. Reboot.

8. Test.
