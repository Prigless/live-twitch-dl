#!/bin/bash





echo """
by default, the script will run following commands:

"stream-dl": "python3 twitch_stream_dl.py",
"chat-dl": "python3 twitch_chat_dl.py",
"discord-bot": "python3 auto_sending_discord_msg.py"


if you wish to change the commands, exit now and run these commands manually or edit the tmux_config.json file
"""

read -p "Press Enter to continue... (or CTRL+C to exit)"





#? Read the JSON file and store the data in variables
session_name=$(cat tmux_config.json | jq -r '.session_name')
session_windows=$(cat tmux_config.json | jq -r '.session_windows | keys[]')
session_windows_commands=$(cat tmux_config.json | jq -r '.session_windows | to_entries[] | .value')

  
#? Convert the session_windows variable into an array
IFS=$'\n' read -d '' -ra session_windows_array <<<"$session_windows"
IFS=$'\n' read -d '' -ra session_windows_commands_array <<<"$session_windows_commands"

  
echo "Session Name: $session_name"
echo "Windows:"
echo "${session_windows_array[*]}"
echo ""
echo "Commands:"
echo "${session_windows_commands_array[*]}"





#? check if the Tmux session exists

# if tmux has-session -t my_sessions | grep -q "can't find session"; then
if tmux has-session -t=$session_name 2>/dev/null; then
    echo "Using Existing: $session_name"
    session_exists=true

else
    echo "Creating: $session_name"
    session_exists=false

    tmux new-session -d -s $session_name

fi


sleep 1



for i in "${!session_windows_array[@]}"; do
    window=${session_windows_array[i]}
    command=${session_windows_commands_array[i]}


    echo "start"
    echo "Window: $window"
    echo "command: $command"
    echo ""


    if tmux list-windows -t $session_name -F '#{window_name}' | grep -q ^$window$; then
        echo "Window Exists: $window"

    else
        echo "Creating Window: $window"
        tmux new-window -t $session_name -n $window "bash -i"
        sleep 1

        command=$(echo "$command" | sed 's/ / Space /g') #? tmux ignores spaces, word "Space" instead is needed
        tmux send-keys -t $session_name $command C-m
    fi
    sleep 1

done

#todo   tmux select-layout -t $session_name:0 tiled

  
tmux attach -t $session_name

  
  
  
  
  

















  

# #!/bin/bash

  

# # Read the JSON file

# json=$(cat tmux_config.json)

  

# # Get the session name

# session_name=$(echo "$json" | jq -r '.session_name')

  

# # Get the window names

# session_windows=$(echo "$json" | jq -r '.session_windows | keys[]')

  

# # Get the window commands

# for window in ${session_windows[@]}; do

# session_windows_commands+=($(echo "$json" | jq -r ".session_windows[\"$window\"]"))

# done

  

# # Print the variables

# for window in "${!session_windows[@]}"; do

# window_commands=(${session_windows_commands[$window]})

# echo "Window Name: $window"

# echo "Commands: ${window_commands[@]}"

# done