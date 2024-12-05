#!/usr/bin/python3
import os
import re
import time
import qrcode
import math
import logging
import subprocess
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306
from PIL import ImageFont
from logging.handlers import RotatingFileHandler

# Battery = -1 means no message received
# Battery in (0, 1.5) means missing jumper cap
# Battery in (3.5, 5.5) means the barrel plug is unplugged
# Battery in (6, 7) means the jumper cap is on 6 V
# Battery in (7, 12) means the jumper cap is on 12 V

# Define constants
SCREEN_CHANGE_DELAY = 3
QR_SCREEN_CHANGE_DELAY = 8
FLASH_INTERVAL = 0.4  # Flash interval in seconds
DIS_WIDTH = 128  # OLED display width, in pixels
DIS_HEIGHT = 64  # OLED display height, in pixels
BATTERY_LIMIT_HIGH = 12  # Volts
BATTERY_LIMIT_LOW = 9
JUMPER_6V_HIGH = 7
JUMPER_6V_LOW = 6
UNPLUG_BARREL_HIGH = 5.5
UNPLUG_BARREL_LOW = 3.5
NO_CAP_HIGH = 1.5
NO_CAP_LOW = 0

# Setup logging
log_file = "/var/log/mbot/mbot_oled.log"
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
        try:
            self.device = ssd1306(i2c(port=1, address=0x3C))
            self.font_large = ImageFont.truetype("/usr/local/etc/arial.ttf", 18)
            self.font = ImageFont.truetype("/usr/local/etc/arial.ttf", 14)
            self.font_small = ImageFont.truetype("/usr/local/etc/arial.ttf", 10)
            self.font_medium = ImageFont.truetype("/usr/local/etc/arial.ttf", 12)
        except Exception as e:
            logging.error(f"Initialization failed: {e}")
            self.device = None
            self.font = None
            self.font_small = None

        self.battery_voltage = -1
        self.ip_str = "IP Not Found"
        self.low_battery_flag = False

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
            return subprocess.check_output(["iwgetid", "-r"]).decode().strip() or "N/A"
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

    def get_wlan0_ip(self):
        try:
            command_output = subprocess.check_output(["ifconfig", "wlan0"]).decode()
            ip_match = re.search(r'inet ([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)', command_output)
            self.ip_str = ip_match.group(1) if ip_match else "IP Not Found"
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to get wlan0 IP: {e}")
            self.ip_str = "Error"

    def get_services(self):
        try:
            services = ["mbot-start-network", "mbot-publish-info", "mbot-rplidar-driver",
                        "mbot-lcm-serial", "mbot-web-server", "mbot-motion-controller", "mbot-slam", "mbot-oled"]
            serv_short_names = ["start-net", "pub-info", "lidar-drv", "lcm-ser", "webapp", "motion", "slam", "oled"]
            result = {}

            for i, service in enumerate(services):
                try:
                    # Capture the status using subprocess and extract the third line equivalent
                    serv_status = subprocess.check_output(
                        f"systemctl status {service} | head -3 | tail -1",
                        shell=True,
                        stderr=subprocess.DEVNULL
                    ).decode().strip()

                    if not serv_status:
                        result[serv_short_names[i]] = "not found"
                    else:
                        keywords = ["loaded", "failed", "active", "inactive"]
                        parts = serv_status.split()
                        activity_str = parts[1] if len(parts) > 1 and parts[1] in keywords else parts[2] if len(parts) > 2 else "unknown"
                        result[serv_short_names[i]] = activity_str

                        if activity_str != "failed" and len(parts) > 2:
                            result[serv_short_names[i]] += f" {parts[2]}"
                        elif activity_str == "failed" and len(parts) > 3:
                            result[serv_short_names[i]] += f" ({parts[3]})"

                except subprocess.CalledProcessError:
                    result[serv_short_names[i]] = "failed"

            return result

        except Exception as e:
            logging.error(f"Failed to get services: {e}")
            return {}

    def get_battery_info(self):
        try:
            # Run the "mbot-status" command
            result = subprocess.run(['mbot-status'], capture_output=True, text=True, check=True)
            # Extract the voltage value from the command output using regex
            match = re.search(r'Battery Voltage:\s*([\d.]+)\s*V', result.stdout)
            if match:
                battery_volt = float(match.group(1))
                self.battery_voltage = battery_volt

                # Set the low battery flag based on the voltage value
                if self.battery_voltage < BATTERY_LIMIT_LOW and self.battery_voltage > JUMPER_6V_HIGH:
                    self.low_battery_flag = True
            else:
                self.battery_voltage = -2  # Unable to parse battery voltage
        except subprocess.CalledProcessError as e:
            logging.error(f"Error executing mbot-status: {e}")
            self.battery_voltage = -2  # Error state

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

    def display_qr_code(self):
        qr_img = self.get_qr_code(f"http://{self.ip_str}")
        qr_x_pos = (DIS_WIDTH - 48) # right aligned

        def draw_qr(draw):
            draw.text((1, 1), "WebApp", font=self.font, fill="white")
            draw.text((1, 49), self.ip_str, font=self.font, fill="white")
            draw.line((0, 48, 127, 48), fill="white")
            draw.bitmap((qr_x_pos, 0), qr_img, fill="white")
        self.draw(draw_qr)

    def get_qr_code(self, ip_str):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(ip_str)
        qr.make(fit=True)
        return qr.make_image(fill_color="black", back_color="white").resize((48, 48))

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

    def display_services(self):
        services = self.get_services()
        serv_short_names = ["start-net", "pub-info", "lidar-drv", "lcm-ser", "webapp", "motion", "slam", "oled"]
        n_screens = math.ceil(len(services) / 3)

        for i in range(n_screens):
            def draw_services(draw):
                draw.text((1, 1), f"{serv_short_names[3*i]}: {services.get(serv_short_names[3*i], 'not found')}", font=self.font_small, fill="white")
                if 3*i+1 < len(services):
                    draw.text((1, 17), f"{serv_short_names[3*i+1]}: {services.get(serv_short_names[3*i+1], 'not found')}", font=self.font_small, fill="white")
                if 3*i+2 < len(services):
                    draw.text((1, 33), f"{serv_short_names[3*i+2]}: {services.get(serv_short_names[3*i+2], 'not found')}", font=self.font_small, fill="white")
                draw.line((0, 48, 127, 48), fill="white")
                draw.text((1, 49), self.ip_str, font=self.font, fill="white")
            self.draw(draw_services)
            time.sleep(SCREEN_CHANGE_DELAY)

    def display_battery_info(self):
        self.get_battery_info()
        def draw_battery(draw):
            if self.battery_voltage < JUMPER_6V_HIGH and self.battery_voltage > JUMPER_6V_LOW:
                draw.text((1, 1), "Voltage Select Jumper 6V", font=self.font_small, fill="white")
                draw.text((1, 24), f"Motor Volt: {self.battery_voltage:.2f} V", font=self.font_medium, fill="white")
            elif self.battery_voltage < UNPLUG_BARREL_HIGH and self.battery_voltage > UNPLUG_BARREL_LOW:
                draw.text((1, 1), f"Control Board", font=self.font, fill="white")
                draw.text((1, 24), f"Not Powered", font=self.font, fill="white")
            elif self.battery_voltage < NO_CAP_HIGH and self.battery_voltage > NO_CAP_LOW:
                draw.text((1, 1), f"Voltage Select Jumper", font=self.font_small, fill="white")
                draw.text((1, 24), f"Not Detected", font=self.font_medium, fill="white")
            elif self.battery_voltage == -1:
                draw.text((1, 1), "Battery Info", font=self.font, fill="white")
                draw.text((1, 24), f"No LCM Message", font=self.font_medium, fill="white")
            elif self.battery_voltage == -2: # error from mbot status
                draw.text((1, 1), "Battery Info", font=self.font, fill="white")
                draw.text((1, 24), "Not Available", font=self.font, fill="white")
            else:
                draw.text((1, 1), "Battery Info", font=self.font, fill="white")
                draw.text((1, 24), f"Voltage: {self.battery_voltage:.2f} V", font=self.font, fill="white")
            draw.line((0, 48, 127, 48), fill="white")
            draw.text((1, 49), self.ip_str, font=self.font, fill="white")
        self.draw(draw_battery)

    def flash_message(self, message):
        invert = False
        while True:
            # Toggle inversion by switching text and background colors
            if invert:
                # Draw inverted (white background, black text)
                self.draw(lambda draw: (
                    draw.rectangle(self.device.bounding_box, outline="white", fill="white"),
                    draw.text((1, 20), message, font=self.font_large, fill="black")
                ))
            else:
                # Draw normal (black background, white text)
                self.draw(lambda draw: draw.text((1, 20), message, font=self.font_large, fill="white"))

            # Toggle invert flag and pause for FLASH_INTERVAL
            invert = not invert
            time.sleep(FLASH_INTERVAL)
            if self.battery_voltage < JUMPER_6V_HIGH:
                self.low_battery_flag = False
                break

    def main_loop(self):
        if self.device is None or self.font is None or self.font_small is None:
            logging.error("Initialization failed. Exiting application.")
            return

        while True:
            try:
                if self.low_battery_flag:
                    self.flash_message("LOW BATTERY")

                self.get_wlan0_ip()

                self.display_wifi_info()
                time.sleep(SCREEN_CHANGE_DELAY)
                self.display_battery_info()
                time.sleep(SCREEN_CHANGE_DELAY)
                self.display_qr_code()
                time.sleep(QR_SCREEN_CHANGE_DELAY)
                self.display_resources()
                time.sleep(SCREEN_CHANGE_DELAY)
                self.display_services()
                time.sleep(SCREEN_CHANGE_DELAY)

            except Exception as e:
                logging.error(f"Unhandled exception during main loop: {e}")
                time.sleep(5)
                continue

if __name__ == '__main__':
    mbot_oled = MBotOLED()
    mbot_oled.main_loop()
