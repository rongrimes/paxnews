#!/usr/bin/bash

# monitor program to keep paxnews2 running

cd /home/pi/python/paxnews

while true
do
	./paxnews2.py
	sleep 2
done
