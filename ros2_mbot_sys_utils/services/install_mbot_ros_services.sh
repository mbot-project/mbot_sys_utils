#!/bin/bash

set -e  # Quit on error.

SERVICE_LIST="mbot-start-network
              mbot-microros-agent
              mbot-oled"

# Copy the scripts we need for the services.
sudo cp mbot_ros_oled_display.py /usr/local/etc/
sudo chmod +x /usr/local/etc/mbot_ros_oled_display.py
sudo cp mbot_start_networking.sh /usr/local/etc/
sudo chmod +x /usr/local/etc/mbot_start_networking.sh

# Copy the services.
for serv in $SERVICE_LIST
do
    sudo cp $serv.service /etc/systemd/system/$serv.service
done

# Enable the services.
sudo systemctl daemon-reload
for serv in $SERVICE_LIST
do
    sudo systemctl enable $serv.service
done

# Success message.
echo
echo "Installed, enabled, and started the following services:"
echo
for serv in $SERVICE_LIST
do
    echo "    $serv.service"
done
echo
