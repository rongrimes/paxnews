#!/usr/bin/bash

# enable the bluetooth keyboard when reguested by paxnews2.py

# bluetooth ID of the TZUMI keyboard.
KBD=20:14:10:6D:D5:69

# Find if the kbd is connected, & use xargs to squash out the space in the string
conn=`bluetoothctl info $KBD | grep Connected | xargs`
split=( $conn )    # convert to an array
#echo ${split[1]} ${split[0]}

if [ "${split[1]}" = "yes" ]
then
	echo \*$conn
	exit # don't need to force connection
fi

bluetoothctl connect $KBD > /dev/null               # connect and...
sleep 1
bluetoothctl info $KBD | grep Connected | xargs     # ...verify.
