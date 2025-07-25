#!/bin/bash

# Define log file path
log_file="/var/log/mbot/mbot_start_networking.log"
mkdir -p $(dirname "$log_file")
chmod 777 $(dirname "$log_file")
touch "$log_file"
chmod 666 "$log_file"

OS=$(cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)
# Determine the OS and set the config file path
if [[ "$OS" == *"Ubuntu"* ]]; then
    config_file="/boot/firmware/mbot_config.txt"
else
    echo "ERROR: Unknown OS!" | tee -a "$log_file"
    exit 1
fi

echo "OS: $OS" | tee -a "$log_file"
echo "Config file path: $config_file" | tee -a "$log_file"

# Check the hardware model
model=$(tr -d '\0' </proc/device-tree/model)
if [[ "$model" == *"Raspberry Pi 5"* ]]; then
    echo "Detected Raspberry Pi 5" | tee -a "$log_file"
    BTLD_PIN=4
    RUN_PIN=17
    GPIO_CHIP="gpiochip4"
else
    echo "ERROR: Unknown hardware!" | tee -a "$log_file"
    exit 1
fi

echo "===== $(date '+%Y-%m-%d %H:%M:%S') =====" | tee -a "$log_file"

# Read values from config file
while IFS='=' read -r key value; do
    case "$key" in
        mbot_hostname) hostname="$value";;
        mbot_ap_password) ap_password="$value";;
        new_wifi_ssid) home_wifi_ssid="$value";;
        new_wifi_password) home_wifi_password="$value";;
        autostart) autostart="$value";;
    esac
done < "$config_file"

ap_ssid="${hostname}-AP"

# Change the hostname in /etc/hosts
chmod 666 /etc/hosts
sed -i "s/$(uname -n)/$hostname/g" /etc/hosts
hostnamectl set-hostname "$hostname"
echo "$hostname" > /etc/hostname
echo "hostname set to '$hostname'" | tee -a "$log_file"

# Check if there is an active WiFi connection
start_ap=false
wifi_status=$(nmcli -t -f NAME,DEVICE,STATE c show --active | grep 'wlan0:activated')
if [[ -n "$wifi_status" ]]; then
    active_wifi_name=$(echo "$wifi_status" | cut -d: -f1)
    echo "Connected to active WiFi network '$active_wifi_name'. Done." | tee -a "$log_file"
else
    echo "Looking for home network '$home_wifi_ssid'" | tee -a "$log_file"
    available_networks=$(nmcli -m multiline --terse --fields BSSID,SSID,CHAN,SIGNAL dev wifi list | grep -v '^IN-USE')

    # Parse available networks and prioritize by signal strength
    while read -r bssid && read -r ssid && read -r channel && read -r signal; do
        bssid=${bssid#*:}
        ssid=${ssid#*:}
        channel=${channel#*:}
        signal=${signal#*:}
        if [[ "$ssid" == "$home_wifi_ssid" ]]; then
            echo "$bssid $ssid $channel $signal" | tee -a "$log_file"
            available_networks_sorted+="$signal $channel $bssid $ssid\n"
        fi
    done <<< "$available_networks"

    sorted_avail=$(echo -e "$available_networks_sorted" | sort -nr)

    if grep -q "$home_wifi_ssid" <<< "$sorted_avail"; then
        if ! nmcli connection show | grep -q "$home_wifi_ssid"; then
            home_wifi_bssid=$(echo "$sorted_avail" | head -n 1 | awk '{print $3}')
            echo "Connecting to BSSID: $home_wifi_bssid" | tee -a "$log_file"
            nmcli device wifi connect "$home_wifi_bssid" password "$home_wifi_password"
        else
            echo "Connecting to SSID: $home_wifi_ssid" | tee -a "$log_file"
            nmcli device wifi connect "$home_wifi_ssid" password "$home_wifi_password"
        fi

        # If not connected, start the access point.
        if ! nmcli device status | grep "$home_wifi_ssid" | grep -q "connected"; then
            echo "Connection failed! Check your password!" | tee -a "$log_file"
            start_ap=true
        fi
    else
        echo "Home network not found." | tee -a "$log_file"
        start_ap=true
    fi
fi

if [[ $start_ap == true ]]; then
    echo "Starting Access Point" | tee -a "$log_file"
    nmcli connection show | grep -q "mbot_wifi_ap" && nmcli connection delete mbot_wifi_ap
    nmcli connection add type wifi ifname '*' con-name mbot_wifi_ap autoconnect no ssid "$ap_ssid"
    nmcli connection modify mbot_wifi_ap 802-11-wireless.mode ap 802-11-wireless.band a ipv4.method shared
    nmcli connection modify mbot_wifi_ap wifi-sec.key-mgmt wpa-psk wifi-sec.psk "$ap_password"
    nmcli connection modify mbot_wifi_ap ipv4.addresses 192.168.3.1/24 ipv4.gateway 192.168.3.1
    echo "Access point created successfully." | tee -a "$log_file"
    sleep 10
    nmcli connection up mbot_wifi_ap
    echo "Access point started." | tee -a "$log_file"
fi

sleep 0.1

case "$autostart" in
    run)
        sudo gpioset "$GPIO_CHIP" "$RUN_PIN"=0
        sudo gpioset "$GPIO_CHIP" "$BTLD_PIN"=1
        sleep 0.1
        sudo gpioset "$GPIO_CHIP" "$RUN_PIN"=1
        sleep 0.1
        echo "Autostart is set to run" | tee -a "$log_file"
        ;;
    bootload)
        sudo gpioset "$GPIO_CHIP" "$BTLD_PIN"=0
        sudo gpioset "$GPIO_CHIP" "$RUN_PIN"=0
        sleep 0.1
        sudo gpioset "$GPIO_CHIP" "$RUN_PIN"=1
        echo "Autostart is set to bootload" | tee -a "$log_file"
        ;;
    disable)
        sudo gpioset "$GPIO_CHIP" "$BTLD_PIN"=1
        sudo gpioset "$GPIO_CHIP" "$RUN_PIN"=0
        sleep 0.1
        echo "Autostart is disabled" | tee -a "$log_file"
        ;;
    *)
        echo "Incorrect input for autostart variable, should be either run or disable" | tee -a "$log_file"
        ;;
esac