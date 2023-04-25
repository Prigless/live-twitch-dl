#!/bin/bash




check_if_exists() {
    path=$1
    type=$2

    if [ "$type" == "file" ]; then
        if [ -f "$path" ]; then
            echo "using existing: $path"
        else
            echo "creating: $path"
            touch $path
        fi
    elif [ "$type" == "dir" ]; then
        if [ -d "$path" ]; then
            echo "using existing: $path"
        else
            echo "creating: $path"
            mkdir $path
        fi
    else
        echo "Invalid type argument. Must be 'file' or 'dir'."
    fi
}



# check_if_exists "$path" "$type"

echo "Creating folders..."


check_if_exists "db" "dir"
check_if_exists "logs" "dir"


check_if_exists "logs/discord_bot.log" "file"
check_if_exists "logs/twitch_chat_dl.log" "file"
check_if_exists "logs/twitch_stream_dl.log" "file"
