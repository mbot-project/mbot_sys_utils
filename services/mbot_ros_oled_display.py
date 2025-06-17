#!/usr/bin/python3
import os
import re
import time
import logging
import subprocess
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306
from PIL import ImageFont
from logging.handlers import RotatingFileHandler

# Define constants
SCREEN_CHANGE_DELAY = 3
DIS_WIDTH = 128  # OLED display width, in pixels
DIS_HEIGHT = 64  # OLED display height, in pixels

# Setup logging
log_file = "/tmp/mbot_ros_oled_display.log"
os.makedirs(os.path.dirname(log_file), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=3),
        logging.StreamHandler()
    ]
)

class MBotOLED:
    def __init__(self):
        # Initialize OLED device and fonts
        self.device = None
        self.font_large = None
        self.font = None
        self.font_small = None
        self.font_medium = None
        
        try:
            logging.info("Attempting to initialize OLED device...")
            self.device = ssd1306(i2c(port=1, address=0x3C))
            logging.info("OLED device initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize OLED device: {e}")
            
        try:
            logging.info("Attempting to load fonts...")
            # Ubuntu 24 optimized fonts for OLED displays
            font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
            
            self.font_large = ImageFont.truetype(font_path, 18)
            self.font = ImageFont.truetype(font_path, 14)
            self.font_small = ImageFont.truetype(font_path, 10)
            self.font_medium = ImageFont.truetype(font_path, 12)
            logging.info(f"Fonts loaded successfully from: {font_path}")
                
        except Exception as e:
            logging.error(f"Failed to load fonts: {e}")
            logging.info("Attempting to use default font...")
            try:
                self.font_large = ImageFont.load_default()
                self.font = ImageFont.load_default()
                self.font_small = ImageFont.load_default()
                self.font_medium = ImageFont.load_default()
                logging.info("Default fonts loaded successfully")
            except Exception as e2:
                logging.error(f"Failed to load default fonts: {e2}")

        # Set up display variables
        self.battery_voltage = -1
        self.ip_str = "IP Not Found"

        # Track the last received message time
        self.last_message_time = time.time()
        self.message_timeout = 10  # Set a threshold in seconds to detect message timeout

    def draw(self, draw_func):
        if self.device:
            with canvas(self.device) as draw:
                draw_func(draw)

    # Information Fetching Methods
    def get_hostname(self):
        try:
            return subprocess.check_output(["hostname"]).decode().strip()
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to get hostname: {e}")
            return "Error"

    def get_uptime(self):
        try:
            uptime_output = subprocess.check_output(["uptime", "-p"]).decode().strip()
            pattern = r'up (\d+) hour[s]*, (\d+) minute[s]*|up (\d+) minute[s]*'
            match = re.match(pattern, uptime_output)

            if match:
                hours, minutes, minutes_only = match.groups()
                return f'{minutes_only}m' if minutes_only else f'{hours}h{minutes}m'
            else:
                return uptime_output[3:]
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to get uptime: {e}")
            return "Error"

    def get_connected_ssid(self):
        try:
            # Try iwgetid first (if available)
            return subprocess.check_output(["/usr/sbin/iwgetid", "-r"]).decode().strip() or "N/A"
        except subprocess.CalledProcessError:
            try:
                # Fallback to nmcli (NetworkManager command line)
                output = subprocess.check_output(["nmcli", "-t", "-f", "active,ssid", "dev", "wifi"]).decode()
                for line in output.strip().split('\n'):
                    if line.startswith('yes:'):
                        return line.split(':', 1)[1] or "N/A"
                return "N/A"
            except subprocess.CalledProcessError as e:
                logging.error(f"Failed to get connected SSID: {e}")
                return "Error"

    def get_mem_free(self):
        try:
            mem_output = subprocess.check_output("free -m | awk 'NR==2{printf \"%.2f%%\", $3*100/$2 }'", shell=True).decode().strip()
            return mem_output
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to get memory usage: {e}")
            return "Error"

    def get_load_avg(self):
        try:
            load_output = subprocess.check_output(["top", "-bn1"]).decode()
            return re.search(r'load average: (.*)', load_output).group(1)
        except (subprocess.CalledProcessError, AttributeError) as e:
            logging.error(f"Failed to get load average: {e}")
            return "Error"

    def get_ip(self):
        try:
            # Try multiple network interface names common in Ubuntu
            interfaces = ["wlan0", "wlp0s20f3", "wifi0"]
            for interface in interfaces:
                try:
                    command_output = subprocess.check_output(["ip", "addr", "show", interface]).decode()
                    ip_match = re.search(r'inet ([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)', command_output)
                    if ip_match:
                        self.ip_str = ip_match.group(1)
                        return
                except subprocess.CalledProcessError:
                    continue
            
            # If no specific interface found, try to get any wireless interface IP
            command_output = subprocess.check_output(["ip", "route", "get", "8.8.8.8"]).decode()
            ip_match = re.search(r'src ([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)', command_output)
            self.ip_str = ip_match.group(1) if ip_match else "IP Not Found"
            
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to get IP: {e}")
            self.ip_str = "Error"

    def battery_info_callback(self, channel, data):
        # TODO: Implement battery info callback
        pass

    # Screen Display Methods
    def display_wifi_info(self):
        ssid = self.get_connected_ssid()
        hostname = self.get_hostname()
        uptime = self.get_uptime()

        def draw_wifi(draw):
            draw.text((1, 1), hostname, font=self.font, fill="white")
            draw.text((1, 17), f"SSID: {ssid}", font=self.font, fill="white")
            draw.text((1, 33), f"Uptime: {uptime}", font=self.font_small, fill="white")
            draw.line((0, 48, 127, 48), fill="white")
            draw.text((1, 49), self.ip_str, font=self.font, fill="white")
        self.draw(draw_wifi)

    def display_resources(self):
        mem_str = self.get_mem_free()
        load_avg_str = self.get_load_avg()

        def draw_resources(draw):
            draw.text((1, 1), "Load Average: ", font=self.font_small, fill="white")
            draw.text((20, 17), load_avg_str, font=self.font_small, fill="white")
            draw.text((1, 33), f"RAM Used: {mem_str}", font=self.font_small, fill="white")
            draw.line((0, 48, 127, 48), fill="white")
            draw.text((1, 49), self.ip_str, font=self.font, fill="white")
        self.draw(draw_resources)

    def display_battery_info(self):
        self.check_message_timeout()
        def draw_battery(draw):
            if self.battery_voltage == -1:
                draw.text((1, 1), "Battery Info", font=self.font, fill="white")
                draw.text((1, 24), f"Voltage: ???", font=self.font, fill="white")
            else:
                draw.text((1, 1), "Battery Info", font=self.font, fill="white")
                draw.text((1, 24), f"Voltage: {self.battery_voltage:.2f} V", font=self.font, fill="white")
            draw.line((0, 48, 127, 48), fill="white")
            draw.text((1, 49), self.ip_str, font=self.font, fill="white")
        self.draw(draw_battery)

    def check_message_timeout(self):
        current_time = time.time()
        if current_time - self.last_message_time > self.message_timeout:
            logging.warning("No new messages received for a while.")
            self.battery_voltage = -1

    def main_loop(self):
        if self.device is None or self.font is None or self.font_small is None:
            logging.error("Initialization failed. Exiting application.")
            return

        while True:
            try:
                self.get_ip()

                self.display_wifi_info()
                time.sleep(SCREEN_CHANGE_DELAY)
                self.display_battery_info()
                time.sleep(SCREEN_CHANGE_DELAY)
                self.display_resources()
                time.sleep(SCREEN_CHANGE_DELAY)

            except Exception as e:
                logging.error(f"Unhandled exception during main loop: {e}")
                time.sleep(5)
                continue

if __name__ == '__main__':
    mbot_oled = MBotOLED()
    mbot_oled.main_loop()
