#!/usr/bin/python3
import os
import re
import time
import qrcode
import math

from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306
from PIL import ImageFont

fontpath = str("/usr/local/etc/arial.ttf")
font = ImageFont.truetype(fontpath, 14)
fontpath = str("/usr/local/etc/arial.ttf")
font_small = ImageFont.truetype(fontpath, 10)

device = ssd1306(i2c(port=1, address=0x3C))

SCREEN_CHANGE_DELAY = 3
QR_SCREEN_CHANGE_DELAY = 8

# ---------------------------------------------Information fetching------------------------------------------------------

# Function to get the IP address of the wlan0 interface
def get_wlan0_ip():
    try:
        # Execute the ifconfig command and capture the output
        command_output = os.popen("ifconfig wlan0").read()
        # Use regular expressions to find the IP address in the output
        ip_match = re.search(r'inet ([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)', command_output)
        if ip_match:
            ip_address = ip_match.group(1)
            return ip_address
        else:
            return None
    except Exception as e:
        return str(e)
    
def get_hostname():
    try:
        command_output = os.popen("hostname").read()
        return command_output.strip()
    except Exception as e:
        return str(e)
    
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
        return str(e)
    
def get_connected_ssid():
    try:
        # Execute the iwgetid command and capture the output
        ssid_output = os.popen("iwgetid -r").read().strip()
        if not ssid_output:
            ssid_output = "N/A"
        return ssid_output
    except Exception as e:
        return str(e)

def get_mem_free():
    try:
        mem_output = os.popen("free -m | awk 'NR==2{printf \"%.2f%%\", $3*100/$2 }'").read()
        return mem_output
    except Exception as e:
        return str(e)
    
def get_load_avg():
    try:
        load_output = os.popen("top -bn1 | grep load | awk '{print \"\", $11, $12, $13}'").read()
        return load_output
    except Exception as e:
        return str(e)

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
    qr_img = qr_img.resize((64, 64))
    return qr_img

services=["mbot-start-network", "mbot-publish-info", "mbot-rplidar-driver", 
          "mbot-lcm-serial", "mbot-web-server", "mbot-motion-controller", "mbot-slam", "mbot-oled"]
serv_short_names = ["start-net", "pub-info", "lidar-drv", "lcm-ser", "webapp", "motion", "slam", "oled"]
def get_services():
    result = dict()
    for i, service in enumerate(services):
        serv_status = os.popen("systemctl status " + service + " | head -3 | tail -1").read()
        if not serv_status:
            result[serv_short_names[i]] = "not found"
        else:
            keywords = ["loaded", "failed", "active", "inactive"]
            activity_str = serv_status.split()[1] if serv_status.split()[1] in keywords else serv_status.split()[2]
            result[serv_short_names[i]] = activity_str
            if activity_str != "failed":
                result[serv_short_names[i]] += " " + serv_status.split()[2]
            else:
                result[serv_short_names[i]] += " (" + serv_status.split()[3]
    return result

#-----------------------------------------------Data Screens-------------------------------------------

def screen_wifi():
    #Get SSID
    SSID_str = get_connected_ssid()
    #Get IP
    IP_str = get_wlan0_ip()
    #Get Hostname
    hostname_str = get_hostname()
    #Get uptime
    uptime_str = get_uptime()
    
    # print it
    with canvas(device) as draw:
        draw.text((1,1), hostname_str, font=font_small, fill="white")
        draw.text((1,17), "SSID: "+ SSID_str, font=font, fill="white")
        draw.text((1,33), "Uptime: "+ uptime_str, font=font, fill="white")
        draw.line((0, 48, 127, 48), fill="white")
        draw.text((1,49), IP_str, font=font, fill="white")

def screen_QR():
    #Get IP
    IP_str = get_wlan0_ip()
    # Split the IP string into two based on the location of the second dot
    # This is done to make the IP address fit on the OLED screen
    IP_str_1 = IP_str[:IP_str.find('.', IP_str.find('.') + 1)+1]
    IP_str_2 = IP_str[IP_str.find('.', IP_str.find('.') + 1)+1:]
    #Get QR code
    qr_img = get_QR_code("http://"+IP_str)
    with canvas(device) as draw:
        draw.text((1,1), "WebApp QR", font=font_small, fill="white")
        draw.line((0, 32, 64, 32), fill="white")
        draw.text((1,33), IP_str_1, font=font, fill="white")
        draw.text((1,49), IP_str_2, font=font, fill="white")
        draw.bitmap((64, 0), qr_img, fill="white")

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
        draw.text((1,49), get_wlan0_ip(), font=font, fill="white")


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
            draw.text((1,49), get_wlan0_ip(), font=font, fill="white")
        time.sleep(SCREEN_CHANGE_DELAY)
       

def main():
    while True:
        screen_wifi()
        time.sleep(SCREEN_CHANGE_DELAY)
        screen_QR()
        time.sleep(QR_SCREEN_CHANGE_DELAY)
        screen_resources()
        time.sleep(SCREEN_CHANGE_DELAY)
        screen_services()

if __name__ == '__main__':
    main()