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
   - On Ubuntu 22.04 and Raspberry Pi 5 this is `/boot/firmware`
    ```bash
    sudo cp mbot_config.txt /boot/firmware
    ```
   - on Raspberry Pi 4 this is just `/boot`:
    ```bash
    sudo cp mbot_config.txt /boot
    ```

4. Copy the correct configuration for your board. If you have an RPi 4, this should be `rpi_config.txt`. For the RPi 5, this should be `rpi5_config.txt`. Select the same folder (`/boot/` or `/boot/firmware/`) as from Step 3.
    ```bash
    sudo cp [rpi_config.txt, rpi5_config.txt] [/boot, /boot/firmware/]
    ```

5. Add the configuration to the main configuration file. Again, select `/boot/` or `/boot/firmware/` and `rpi_config.txt` or `rpi5_config.txt` depending on your configuration.
    ```bash
    sudo nano /boot/firmware/config.txt
    # OR
    sudo nano /boot/config.txt
    ```

    Then add the following line under the `[all]` section:
    ```
    [all]
    include rpi5_config.txt
    ```
    Make sure to replace the above with `rpi_config.txt` if you are using the RPi 4.

6. Edit the configuration:
    ```bash
    sudo nano [/boot/mbot_config.txt, /boot/firmware/mbot_config.txt]
    ```

7. Install udev rules:
    ```bash
    cd udev_rules
    ./install_rules.sh
    ```

8. Install services:
    ```bash
    cd services
    ./install_mbot_services.sh
    ```

9. Reboot.

10. Test.
