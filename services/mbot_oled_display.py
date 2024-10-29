#!/usr/bin/python3
import os
import re
import time
import qrcode
import math
import logging
import lcm
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306
from PIL import ImageFont

# Defind constants
SCREEN_CHANGE_DELAY = 3
QR_SCREEN_CHANGE_DELAY = 8
DIS_WIDTH = 128 # OLED display width, in pixels
DIS_HEIGHT = 64 # OLED display height, in pixels
BATTERY_LIMIT = 7 # Volts

# Define global variable
serv_short_names = ["start-net", "pub-info", "lidar-drv", "lcm-ser", "webapp", "motion", "slam", "oled"]
battery_voltage = -1
ip_str = "IP Not Found"
mbot_lcm_installed = False

# Import mbot_lcm_msgs if available
try:
    from mbot_lcm_msgs.mbot_analog_t import mbot_analog_t
    mbot_lcm_installed = True
except ImportError:
    mbot_lcm_installed = False
    logging.warning("ImportError. Battery information will not be available.")

# Setup logging
log_file = "/var/log/mbot/mbot_oled.log"
os.makedirs(os.path.dirname(log_file), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

# Define fonts
try:
    fontpath = str("/usr/local/etc/arial.ttf")
    font = ImageFont.truetype(fontpath, 14)
    font_small = ImageFont.truetype(fontpath, 10)
except Exception as e:
    logging.error(f"Failed to load fonts: {e}")
    font = None
    font_small = None

# Initialize OLED device
try:
    device = ssd1306(i2c(port=1, address=0x3C))
except Exception as e:
    logging.error(f"Failed to initialize OLED device: {e}")
    device = None

# ---------------------------------------------Information fetching------------------------------------------------------

# Function to get the IP address of the wlan0 interface
def get_wlan0_ip():
    global ip_str
    try:
        # Execute the ifconfig command and capture the output
        command_output = os.popen("ifconfig wlan0").read()
        # Use regular expressions to find the IP address in the output
        ip_match = re.search(r'inet ([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)', command_output)
        if ip_match:
            ip_str = ip_match.group(1)
        else:
            ip_str = "IP Not Found"
    except Exception as e:
        logging.error(f"Failed to get wlan0 IP: {e}")
        ip_str = "Error"

def get_hostname():
    try:
        command_output = os.popen("hostname").read()
        return command_output.strip()
    except Exception as e:
        logging.error(f"Failed to get hostname: {e}")
        return "Error"

def get_uptime():
    try:
        uptime_output = os.popen("uptime -p").read().strip()
        # Use regular expressions to extract hours and minutes
        pattern = r'up (\d+) hour[s]*, (\d+) minute[s]*|up (\d+) minute[s]*'
        match = re.match(pattern, uptime_output)

        if match:
            # Extract hours and minutes
            hours, minutes, minutes_only = match.groups()

            if minutes_only is not None:
                # If only minutes are provided
                formatted_str = f'{minutes_only}m'
            else:
                # If both hours and minutes are provided
                formatted_str = f'{hours}h{minutes}m'

            return formatted_str
        else:
            return uptime_output[3:]
    except Exception as e:
        logging.error(f"Failed to get uptime: {e}")
        return "Error"

def get_connected_ssid():
    try:
        # Execute the iwgetid command and capture the output
        ssid_output = os.popen("iwgetid -r").read().strip()
        if not ssid_output:
            ssid_output = "N/A"
        return ssid_output
    except Exception as e:
        logging.error(f"Failed to get connected SSID: {e}")
        return "Error"

def get_mem_free():
    try:
        mem_output = os.popen("free -m | awk 'NR==2{printf \"%.2f%%\", $3*100/$2 }'").read()
        return mem_output
    except Exception as e:
        logging.error(f"Failed to get memory usage: {e}")
        return "Error"

def get_load_avg():
    try:
        load_output = os.popen("top -bn1 | grep load | awk '{print \"\", $11, $12, $13}'").read()
        return load_output
    except Exception as e:
        logging.error(f"Failed to get load average: {e}")
        return "Error"

def get_QR_code(IP: str):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(IP)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    qr_img = qr_img.resize((48,48))
    return qr_img

def get_services():
    try:
        services = ["mbot-start-network", "mbot-publish-info", "mbot-rplidar-driver",
                    "mbot-lcm-serial", "mbot-web-server", "mbot-motion-controller", "mbot-slam", "mbot-oled"]
        serv_short_names = ["start-net", "pub-info", "lidar-drv", "lcm-ser", "webapp", "motion", "slam", "oled"]
        result = dict()
        for i, service in enumerate(services):
            serv_status = os.popen(f"systemctl status {service} | head -3 | tail -1").read().strip()
            if not serv_status:
                result[serv_short_names[i]] = "not found"
            else:
                keywords = ["loaded", "failed", "active", "inactive"]
                activity_str = serv_status.split()[1] if serv_status.split()[1] in keywords else serv_status.split()[2]
                result[serv_short_names[i]] = activity_str
                if activity_str != "failed":
                    result[serv_short_names[i]] += f" {serv_status.split()[2]}"
                else:
                    result[serv_short_names[i]] += f" ({serv_status.split()[3]})"
        return result
    except Exception as e:
        logging.error(f"Failed to get services: {e}")
        return {}

def battery_info_callback(channel, data):
    if mbot_lcm_installed:
        global battery_voltage
        battery_info = mbot_analog_t.decode(data)
        battery_voltage = battery_info.volts[3]

#-----------------------------------------------Data Screens-------------------------------------------

def screen_wifi():
    #Get SSID
    SSID_str = get_connected_ssid()
    #Get Hostname
    hostname_str = get_hostname()
    #Get uptime
    uptime_str = get_uptime()

    # print it
    with canvas(device) as draw:
        draw.text((1,1), hostname_str, font=font, fill="white")
        draw.text((1,17), "SSID: "+ SSID_str, font=font, fill="white")
        draw.text((1,33), "Uptime: "+ uptime_str, font=font_small, fill="white")
        draw.line((0, 48, 127, 48), fill="white")
        draw.text((1,49), ip_str, font=font, fill="white")

def screen_QR():
    #Get QR code
    qr_img = get_QR_code("http://"+ip_str)
    qr_x_pos = (DIS_WIDTH - 48)  # right aligned

    with canvas(device) as draw:
        draw.text((1,1), "WebApp", font=font, fill="white")
        draw.text((1,49), ip_str, font=font, fill="white")
        draw.line((0, 48, 127, 48), fill="white")
        draw.bitmap((qr_x_pos, 0), qr_img, fill="white")

def screen_resources():
    #Get Mem
    mem_str = get_mem_free()
    #Get load avg
    load_avg_str = get_load_avg()
    with canvas(device) as draw:
        draw.text((1,1), "Load Average: ", font=font_small, fill="white")
        draw.text((20,17), load_avg_str, font=font_small, fill="white")
        draw.text((1,33), "RAM Used: " + mem_str, font=font_small, fill="white")
        draw.line((0, 48, 127, 48), fill="white")
        draw.text((1,49), ip_str, font=font, fill="white")

def screen_services():
    services = get_services()
    n_screens = math.ceil(len(services) / 3)
    for i in range(n_screens):
        with canvas(device) as draw:
            draw.text((1,1), serv_short_names[3*i] + ": " + services[serv_short_names[3*i]], font=font_small, fill="white")
            if 3*i+1 < len(services):
                draw.text((1,17), serv_short_names[3*i+1] + ": " + services[serv_short_names[3*i+1]], font=font_small, fill="white")
            if 3*i+2 < len(services):
                draw.text((1,33), serv_short_names[3*i+2] + ": " + services[serv_short_names[3*i+2]], font=font_small, fill="white")
            draw.line((0, 48, 127, 48), fill="white")
            draw.text((1,49), ip_str, font=font, fill="white")
        time.sleep(SCREEN_CHANGE_DELAY)

def screen_battery():
    with canvas(device) as draw:
        draw.text((1, 1), "Battery Info", font=font, fill="white")
        if mbot_lcm_installed:
            draw.text((1, 24), f"Voltage: {battery_voltage:.2f} V", font=font, fill="white")
        else:
            draw.text((1, 24), f"Not Available", font=font, fill="white")
        draw.line((0, 48, 127, 48), fill="white")
        draw.text((1, 49), ip_str, font=font, fill="white")

def main():
    if device is None or font is None or font_small is None:
        logging.error("Initialization failed. Exiting application.")
        return

    lc = lcm.LCM("udpm://239.255.76.67:7667?ttl=0")
    lc.subscribe("MBOT_ANALOG_IN", battery_info_callback)

    logged_service_start = False
    global ip_str
    while True:
        try:
            lc.handle()
            if mbot_lcm_installed:
                if battery_voltage > BATTERY_LIMIT:
                    get_wlan0_ip()  # Update the global IP address
                else:
                    ip_str = "Low Battery"+f" {battery_voltage:.2f}"
            else:
                get_wlan0_ip()  # Update the global IP address

            screen_wifi()
            time.sleep(SCREEN_CHANGE_DELAY)
            screen_battery()
            time.sleep(SCREEN_CHANGE_DELAY)
            screen_QR()
            time.sleep(QR_SCREEN_CHANGE_DELAY)
            screen_resources()
            time.sleep(SCREEN_CHANGE_DELAY)
            screen_services()
            if not logged_service_start:
                logging.info("OLED service started successfully.")
                logged_service_start = True
        except Exception as e:
            logging.error(f"Unhandled exception during main loop: {e}")
            time.sleep(5) # in case just a glitch
            continue

if __name__ == '__main__':
    main()