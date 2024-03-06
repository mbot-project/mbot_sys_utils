services=("mbot-start-network.service" "mbot-publish-info.service" "mbot-rplidar-driver.service" "mbot-lcm-serial.service" "mbot-web-server.service" "mbot-motion-controller.service" "mbot-slam.service" "mbot-oled.service")

# Grab the third line
for service in "${services[@]}"; do
    echo "$service"
    systemctl status $service | head -3 | tail -1
done