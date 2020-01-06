#!/usr/bin/env bash

script_root=~/my-script_root/path

logfile=${HOME}/foodbot.log

channel=bot_test
#channel=tallinn-lunch

cd $script_root

run_daily() {
    python3 foodbot_main.py -channel ${channel} >> "${logfile}"
}

send_text_from_file(){
    custom_path=$script_root/slack_foodbot/resources/custom.msg
    python3 foodbot_main.py -channel ${channel} -custom_path "${custom_path}" #>> "${logfile}"
}

send_image() {
    image_path=${script_root}/slack_foodbot/resources/test-cat.jpeg
    python3 foodbot_main.py -channel ${channel} -image_path "${image_path}" #>> "${logfile}"
}

run_daily
#run_send_image
#run_send_custom
