#!/bin/bash


echo "Welcome to the live-twitch-dl setup script."
read -p "Press Enter to continue..."

echo ""

sleep 2



#? creates folders for logs and db
source shell_scripts/create_folders.sh


#? checks if tmux will be used
source shell_scripts/check_for_tmux.sh


#? create tmux sessions
source shell_scripts/create_tmux_sessions.sh