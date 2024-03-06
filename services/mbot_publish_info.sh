#!/bin/bash

set -e  # Quit on error.

wait_for_ip() {
    echo "Waiting $TIMEOUT seconds for IP..." &>> $LOG
    count=0
    while [ -z $IP ]; do
        if [ $count -gt $TIMEOUT ]; then
            echo "Timed out waiting for IP. Exiting." &>> $LOG
            exit 0
        fi
        sleep 1
        IP=$(hostname -I | awk '{print $1}')
        count=$((count+1))
    done
    echo "Got IP after $count seconds." &>> $LOG
}

HOSTNAME=$(hostname)
IP=$(hostname -I | awk '{print $1}')
LOG_PATH="/var/log/mbot"
mkdir -p $LOG_PATH
LOG="$LOG_PATH/mbot_publish_info.log"
if [ "$(lsb_release -is)" = "Ubuntu" ]; then
    CONFIG_FILE="/boot/firmware/mbot_config.txt"
    IP_OUT_FILE="/boot/firmware/ip_out.txt"
else
    CONFIG_FILE="/boot/mbot_config.txt"
    IP_OUT_FILE="/boot/ip_out.txt"
fi
GIT_USER=$(grep "^mbot_ip_list_user=" $CONFIG_FILE | cut -d'=' -f2)
GIT_TOKEN=$(grep "^mbot_ip_list_token=" $CONFIG_FILE | cut -d'=' -f2)
GIT_URL=$(grep "^mbot_ip_list_url=" $CONFIG_FILE | cut -d'=' -f2)
GIT_ADDR=${GIT_URL#*://}
GIT_PATH="/var/tmp/mbot_ip_registry"
TIMEOUT=30

echo $(date) &>> $LOG
echo "Updating IP" &>> $LOG
echo "Hostname= $HOSTNAME" &>> $LOG
if [ -z $IP ]; then
    wait_for_ip
fi
echo "IP= $IP" &>> $LOG
echo "My IP is $IP!" > $IP_OUT_FILE

if [ ! -d "$GIT_PATH" ]; then
    git clone --depth=1 "https://$GIT_USER:$GIT_TOKEN@$GIT_ADDR" "$GIT_PATH"
fi

git -C $GIT_PATH config --local user.email "$GIT_USER"
git -C $GIT_PATH config --local user.name "$GIT_USER"
#git config pull.rebase false
git -C $GIT_PATH pull https://$GIT_USER:$GIT_TOKEN@$GIT_ADDR &>> $LOG

echo "Calling python script" &>> $LOG
python3 $GIT_PATH/register_mbot.py -hostname $HOSTNAME -ip $IP -log $LOG
echo "Adding..." &>> $LOG
git -C $GIT_PATH/ add data/$HOSTNAME.json &>> $LOG
echo "Committing..." &>> $LOG
git -C $GIT_PATH/ commit -m "Auto update $HOSTNAME IP" &>> $LOG
echo "Pushing..." &>> $LOG
git -C $GIT_PATH/ push https://$GIT_USER:$GIT_TOKEN@$GIT_ADDR &>> $LOG
echo "Deleting local copy..." &>> $LOG
rm -rf $GIT_PATH
echo "Done, exiting" &>> $LOG
exit 0
