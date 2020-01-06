#!/usr/bin/env bash

channel=bot_test
#channel=tallinn-lunch

run_script() {
    (cd ~/path/to/script/folder && python3 foodbot_app.py -channel ${channel} "${@}") #>> "${logfile}")
}

run_daily() {
    run_script
}

send_text_from_file() {
    custom_path=~/path/to/some/file/custom.msg
    run_script -custom_path "${custom_path}"
}

send_image() {
    image_path=~/Desktop/test-cat.jpeg
    run_script -image_path "${image_path}"
}

run_daily
#send_image
#send_text_from_file
