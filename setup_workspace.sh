#!/bin/bash
set -e

# Check if directory argument is provided
if [ -z "$1" ]; then
    echo "Please provide the top level directory as an argument. Usage:"
    echo
    echo "   ./setup_workspace.sh [PATH/TO/WS]"
    echo
    exit 1
fi

TOP_DIR=$1
mkdir -p $TOP_DIR
cd $TOP_DIR

repos=("mbot_lcm_base" "mbot_firmware" "mbot_bridge" "mbot_autonomy" "mbot_gui" "mbot_web_app" "rplidar_lcm_driver" "Documentation")

for repo in "${repos[@]}"; do
  if [ -d "$TOP_DIR/$repo" ]; then
    echo "Repo $TOP_DIR/$repo already exists, pulling latest changes"
    cd $TOP_DIR/$repo
    git pull
  else
    cd $TOP_DIR
    git clone "https://github.com/MBot-Project-Development/$repo.git"
    echo
  fi
done

echo "Done! All repos are in $TOP_DIR"
