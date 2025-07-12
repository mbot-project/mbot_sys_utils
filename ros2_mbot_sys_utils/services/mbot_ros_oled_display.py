#!/usr/bin/python3
import os
import re
import time
import logging
import subprocess
import threading
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306
from PIL import ImageFont
from logging.handlers import RotatingFileHandler
import signal

import rclpy
from rclpy.node import Node
# Attempt to import the custom BatteryADC message. If it is unavailable we will
# continue to run the application, but omit the battery-level subscription.
try:
    from mbot_interfaces.msg import BatteryADC
    BATTERY_SUPPORT = True
except ImportError as e:
    BatteryADC = None  # type: ignore  # Placeholder so the name is defined
    BATTERY_SUPPORT = False

# Define constants
SCREEN_CHANGE_DELAY = 3
DIS_WIDTH = 128  # OLED display width, in pixels
DIS_HEIGHT = 64  # OLED display height, in pixels

# Setup logging
log_file = "/var/log/mbot/mbot_ros_oled_display.log"
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
        self.font = None
        self.font_small = None
        
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
            
            self.font = ImageFont.truetype(font_path, 14)
            self.font_small = ImageFont.truetype(font_path, 10)
            logging.info(f"Fonts loaded successfully from: {font_path}")
                
        except Exception as e:
            logging.error(f"Failed to load fonts: {e}")
            logging.info("Attempting to use default font...")
            try:
                self.font = ImageFont.load_default()
                self.font_small = ImageFont.load_default()
                logging.info("Default fonts loaded successfully")
            except Exception as e2:
                logging.error(f"Failed to load default fonts: {e2}")

        # Set up display variables
        self.battery_voltage = -1
        self.ip_str = "IP Not Found"

        # Track the last received message time
        self.last_message_time = time.time()
        self.message_timeout = 10  # Set a threshold in seconds to detect message timeout

        # Initialize ROS 2 subscription in a background thread
        try:
            rclpy.init(args=None)
            self.ros_node = Node('mbot_oled_display')
            # Subscribe to the battery topic published by the firmware
            if BATTERY_SUPPORT:
                self.ros_node.create_subscription(
                    BatteryADC,
                    'battery_adc',  # Topic name must match the publisher in mbot firmware
                    self.battery_info_callback,
                    10  # QoS depth
                )
                logging.info("Battery subscription created successfully.")
            else:
                logging.info("BatteryADC message not available; skipping battery subscription.")

            # Inform the user if battery support is unavailable
            if not BATTERY_SUPPORT:
                logging.warning("BatteryADC message not found. Battery display will be disabled, but the rest of the UI will function.")

            # Spin the ROS node in a daemon thread so our main loop can run concurrently
            self.ros_spin_thread = threading.Thread(target=rclpy.spin, args=(self.ros_node,), daemon=True)
            self.ros_spin_thread.start()
            logging.info("ROS 2 node started")

            # Simple signal handler for fast quit
            signal.signal(signal.SIGTERM, self._fast_quit)
            signal.signal(signal.SIGINT, self._fast_quit)
        except Exception as e:
            logging.error(f"Failed to initialize ROS 2 subscription: {e}")
            # Make sure rclpy is shutdown cleanly if initialization partially succeeded
            try:
                rclpy.shutdown()
            except Exception:
                pass
            self.ros_node = None

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

    def battery_info_callback(self, msg):
        self.battery_voltage = msg.volts[3]
        self.last_message_time = time.time()

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
        if BATTERY_SUPPORT:
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
            logging.debug("Battery topic timeout – showing ??? on display.")
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

    # ------------------------- Fast-Quit Signal Handler -------------------------
    def _fast_quit(self, signum, frame):
        """Terminate the process quickly on SIGTERM/SIGINT while letting ROS shutdown."""
        logging.info(f"Received signal {signum}; shutting down OLED service immediately.")
        try:
            rclpy.shutdown()
        except Exception:
            pass
        os._exit(0)

if __name__ == '__main__':
    mbot_oled = MBotOLED()
    mbot_oled.main_loop()
