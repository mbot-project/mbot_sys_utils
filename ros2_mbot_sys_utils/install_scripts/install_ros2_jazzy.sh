#!/bin/bash

echo "Starting ROS 2 Jazzy installation..."

# Set up locale
locale  # check for UTF-8
sudo apt update && sudo apt install -y locales
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8
locale  # verify settings

# Add universe repository
sudo apt install software-properties-common -y
sudo add-apt-repository universe -y

# Clean up any broken packages first
echo "Cleaning up broken packages..."
sudo apt --fix-broken install -y
sudo apt autoremove -y
sudo apt autoclean

# Clear package cache
sudo apt clean

# Update package lists
sudo apt update

# Install curl if not present
sudo apt install curl -y

# Set up ROS 2 apt repository
echo "Setting up ROS 2 apt repository..."
export ROS_APT_SOURCE_VERSION=$(curl -s https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest | grep -F "tag_name" | awk -F\" '{print $4}')
curl -L -o /tmp/ros2-apt-source.deb "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${ROS_APT_SOURCE_VERSION}/ros2-apt-source_${ROS_APT_SOURCE_VERSION}.$(. /etc/os-release && echo $VERSION_CODENAME)_all.deb"

# Remove any existing broken installation
sudo dpkg --remove --force-depends ros2-apt-source 2>/dev/null || true
sudo dpkg -i /tmp/ros2-apt-source.deb

# Update package lists again
echo "Updating package lists..."
sudo apt update

# Fix any broken dependencies
sudo apt --fix-broken install -y

# Upgrade existing packages
echo "Upgrading existing packages..."
sudo apt upgrade -y

# Install all ROS 2 packages
echo "Installing all ROS 2 packages..."
sudo apt install -y \
    ros-jazzy-ros-base \
    ros-jazzy-rqt* \
    ros-jazzy-rviz2 \
    ros-jazzy-joint-state-publisher \
    ros-jazzy-xacro \
    ros-jazzy-teleop-twist-keyboard \
    ros-jazzy-tf-transformations \
    ros-jazzy-navigation2 \
    ros-jazzy-nav2-bringup \
    ros-jazzy-slam-toolbox

# Final cleanup
echo "Final cleanup..."
sudo apt --fix-broken install -y
sudo apt autoremove -y

# Set up environment
echo "Setting up environment..."
echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
echo "export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST" >> ~/.bashrc

# Source the setup file for current session
source /opt/ros/jazzy/setup.bash

echo "Installation complete!"
echo "Please run 'source ~/.bashrc' or open a new terminal to use ROS 2."

# Verify installation
echo "Verifying installation..."
if command -v ros2 &> /dev/null; then
    echo "✓ ROS 2 CLI tools installed successfully"
    ros2 --version
else
    echo "✗ ROS 2 CLI tools not found"
fi

echo "Installation finished. Check the output above for any errors."