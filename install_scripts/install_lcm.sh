#!/bin/bash

set -e  # Quit on error.

echo "Installing LCM..."

# Download the LCM file.
wget https://github.com/lcm-proj/lcm/archive/refs/tags/v1.5.0.tar.gz
tar -xzf v1.5.0.tar.gz

# Install LCM.
cd lcm-1.5.0
mkdir build
cd build
cmake ..
make -j4
sudo make install

echo
echo "Installing LCM for Python..."
echo
cd ../lcm-python
sudo python3 setup.py install

# Clean up.
echo
echo "Cleaning up..."
echo
cd ../..
rm v1.5.0.tar.gz
sudo rm -rf lcm-1.5.0/  # Sudo needed for the Python files.

echo 
echo "Increasing UDP buffer size..."
echo
echo "net.core.rmem_max=2097152" | sudo tee -a /etc/sysctl.conf
echo "net.core.rmem_default=2097152" | sudo tee -a /etc/sysctl.conf

echo
echo "Done! LCM is now installed."
