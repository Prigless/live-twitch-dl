#!/bin/bash


echo ""
echo ""

if type tmux > /dev/null 2>&1; then
    echo "tmux is present on the system."
    tmux_present="yes"

else
    echo "tmux is not present on the system."
    tmux_present="no"

fi


instructions () {

echo """

Look at the tmux_config.json and run these commands in your desired way

"""

}


if [ "$tmux_present" = "no" ]; then
    echo "If you do not wish to use tmux, press CTRL+C to exit this script and follow the instructions printed to the console:"
    instructions

    read -p "Press Enter to exit..."
    exit 0


else
    while true; do
        echo ""
        echo "If you do not wish to use tmux, type \"no\"."
        echo "Otherwise, type \"yes\" to continue."
        
        read input
        if [ "$input" = "yes" ]; then
            break

        elif [ "$input" = "no" ]; then
            instructions

            read -p "Press Enter to exit..."
            exit 0
        
        else
            :
        fi
    done
    
fi