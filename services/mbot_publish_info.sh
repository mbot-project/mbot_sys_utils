#!/bin/bash

set -e  # Quit on error.

wait_for_ip() {
    echo "Waiting $TIMEOUT seconds for IP..." | tee -a $LOG
    count=0
    while [ -z $IP ]; do
        if [ $count -gt $TIMEOUT ]; then
            echo "Timed out waiting for IP. Exiting." | tee -a $LOG
            exit 0
        fi
        sleep 1
        IP=$(hostname -I | awk '{print $1}')
        count=$((count+1))
    done
    echo "Got IP after $count seconds." | tee -a $LOG
}

push_to_git() {
    if [ -d "$GIT_PATH" ]; then
        rm -rf $GIT_PATH
    fi

    git clone --depth=1 "https://$GIT_USER:$GIT_TOKEN@$GIT_ADDR" "$GIT_PATH" | tee -a $LOG

    git -C $GIT_PATH config --local user.email "$GIT_USER"
    git -C $GIT_PATH config --local user.name "$GIT_USER"
    #git config pull.rebase false
    git -C $GIT_PATH pull https://$GIT_USER:$GIT_TOKEN@$GIT_ADDR | tee -a $LOG

    echo "Calling python script" | tee -a $LOG
    python3 $GIT_PATH/register_mbot.py -hostname $HOSTNAME -ip $IP -log $LOG
    echo "Adding..." | tee -a $LOG
    git -C $GIT_PATH/ add data/$HOSTNAME.json | tee -a $LOG
    echo "Committing..." | tee -a $LOG
    git -C $GIT_PATH/ commit -m "Auto update $HOSTNAME IP" | tee -a $LOG
    echo "Pushing..." | tee -a $LOG
    git -C $GIT_PATH/ push https://$GIT_USER:$GIT_TOKEN@$GIT_ADDR | tee -a $LOG
    echo "Deleting local copy: $GIT_PATH" | tee -a $LOG
    rm -rf $GIT_PATH
}

HOSTNAME=$(hostname)
IP=$(hostname -I | awk '{print $1}')
LOG_PATH="/var/log/mbot"
mkdir -p $LOG_PATH
LOG="$LOG_PATH/mbot_publish_info.log"
if [ -f "/boot/mbot_config.txt" ]; then
    CONFIG_FILE="/boot/mbot_config.txt"
    IP_OUT_FILE="/boot/ip_out.txt"
elif [ -f "/boot/firmware/mbot_config.txt" ]; then
    CONFIG_FILE="/boot/firmware/mbot_config.txt"
    IP_OUT_FILE="/boot/firmware/ip_out.txt"
else
    echo "ERROR: No MBot configuration file found." | tee -a $LOG
    exit 1
fi

# Grab Git information.
GIT_USER=$(grep "^mbot_ip_list_user=" $CONFIG_FILE | cut -d'=' -f2)
GIT_TOKEN=$(grep "^mbot_ip_list_token=" $CONFIG_FILE | cut -d'=' -f2)
GIT_URL=$(grep "^mbot_ip_list_url=" $CONFIG_FILE | cut -d'=' -f2)
GIT_ADDR=${GIT_URL#*://}
GIT_PATH="/var/tmp/mbot_ip_registry"
TIMEOUT=30

echo $(date) | tee -a $LOG
echo "Updating IP" | tee -a $LOG
echo "Hostname= $HOSTNAME" | tee -a $LOG
if [ -z $IP ]; then
    wait_for_ip
fi

# Write the IP to the SD card.
echo "IP= $IP" | tee -a $LOG
echo "Writing IP to log file: $IP_OUT_FILE"
echo "My IP is $IP!" > $IP_OUT_FILE

# Push to Git repo only if the information was provided.
if [ -z $GIT_USER ] || [ -z $GIT_TOKEN ] || [ -z $GIT_URL ]; then
    echo "Git information not provided, not pushing IP information." | tee -a $LOG
else
    push_to_git
fi

echo "Done, exiting" | tee -a $LOG
exit 0
