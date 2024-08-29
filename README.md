# MBot System Utilities
Install scripts and utilities for setting up an MBot environment.

This has been tested on Raspberry Pi OS (Debain 12, bookworm), on the Raspberry Pi 4 and 5.

## Setting up a fresh image

To set up a new image, get the latest Raspberry Pi OS (Debian 12, bookworm) from the [Raspberry Pi website](https://www.raspberrypi.com/software/operating-systems/). Flash the image onto an SD card, then plug in a monitor, keyboard, and mouse into your Raspberry Pi, boot, and set the desired configurations. The default login information is:
* User: `mbot`
* Password: `i<3robots!`

### Installing Dependencies and System Utilities

You will need to clone this repository after first boot. Then, follow these steps to set up the Raspberry Pi:

1. Install dependencies using scripts in install_scripts directory.
    ```bash
    sudo ./install_scripts/install_mbot_dependencies.sh
    ./install_scripts/install_lcm.sh
    ./install_scripts/install_picosdk.sh
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
5. Install the firmware upload script
    ```bash
    sudo cp mbot-upload-firmware /usr/local/bin
    ```

6. Install udev rules:
    ```bash
    cd udev_rules
    ./install_rules.sh
    ```

7. Install services:
    ```bash
    cd services
    ./install_mbot_services.sh
    ```

8. Configure the Raspberry Pi to enable SSH and use X11 (needed for NoMachine):
   ```bash
   sudo raspi-config
   ```
   Then from the menu, change two configurations:
   * Interface Options -> SSH -> Enable
   * Advanced Options -> Wayland -> X11 (important for NoMachine)
     
9. Reboot.

You're done! The robot should now have the networking services installed and should either connect to the configured network or start up an access point.
