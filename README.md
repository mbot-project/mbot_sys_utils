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

3. Copy mbot_config.txt to the proper loacation in the boot folder. On Ubuntu 22.04 this is `/boot/firmware`, on Raspberry Pi OS this is just `/boot`:
```bash
sudo cp mbot_config.txt [/boot, /boot/firmware]
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

8. Test
