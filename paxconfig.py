#! /usr/bin/python3

import time
import sys
import subprocess
from paxlib import *
#from keypadlib import *
import wifilib

#-----------------------------------------------------------------
admin_level = False          # Enable (via "7") to shutdown paxnews
wifi = wifilib.Wifi()

def config_help():
    '''show config commands'''
    linesegments = []
    linesegments.append("1=Show Uptime")
    linesegments.append("2=Wifi status")
    linesegments.append("3=Wifi config")
    linesegments.append("4=Sw. backlight")
    linesegments.append("7=Set admin lvl")
    linesegments.append("8=Reboot")
    linesegments.append("9=Shutdown")
    linesegments.append("*=Exit Config")

#   Ignore key press value
    display_lines(linesegments, 3)
    clear_screen(0.5)

def config_mypi():
    global keypad
    global pax_2x16_backlight

    while True:
        clear_screen(0.5)
        linesegments = []
        linesegments.append("config>")
        linesegments.append("0=Help Config")
        display_lines(linesegments, 0)      # Delay = 0 - only 2 lines

        # Wait for key pressed
#       double = wait_key()
        double = False
#       keyvalue = keypad.key
        keyvalue = wait_key()

        if   keyvalue == "0":             # Show Help message
            config_help()
        if   keyvalue == "1":             # Show uptime
            uptime()
        elif keyvalue == "2":             # Show my IP address.
            get_IP2()
        elif keyvalue == "3":             # Wifi config
            wifi.wifi_config()
        elif keyvalue == "4":             # Switch backlight
            pax_2x16_backlight= switch_backlight(pax_2x16_backlight) # True = On
        elif keyvalue == "7":
            toggle_admin()
        elif keyvalue == "8":             # Reboot
            shutdown("reboot")
        elif keyvalue == "9":             # Shutdown (poweroff)
            shutdown("shutdown")
        elif keyvalue == "*":             # exit Config
            return
        else:
            continue

#--------------------------------------------------------------------------

def up_compress(uptime):
    ''' trims days, hours minutes to d h m'''
    u = uptime.split()
    new = ""
    for s in u:
        if s.startswith("week"):   # "week," "weeks,"
            new += last + "w "
        elif s.startswith("day"):           # "day," "days," 
            new += last + "d "
        elif s.startswith("hour"):        # etc...
            new += last + "hrs "
        elif s.startswith("minute"):
            new += last + "m"
        else:
            last = s
    return new

def uptime():
    myhost = '/usr/bin/uptime -p'    # -p: pretty - only uptime values
#   Example:  16:52:34 up 3 days, 19:00,  2 users,  load average: 0.00, 0.03, 0.05
#   Example: up 3 minutes 
#            up 4 days, 13 hours, 26 minutes

    pid = subprocess.Popen(myhost, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    s_stdout = pid.stdout.readlines()   # appears we can only call this one time
    s_stdout = s_stdout[0]              # Get single list entry of a byte string
    s_stdout = s_stdout.decode("utf-8").strip()   # Convert to a string & trim
    uplist = s_stdout[3:]           # trim off initial "up"
#   print(uplist) 

    linesegments = ["Uptime:"]
    if len(uplist) > 16:
       linesegments.append(up_compress(uplist))
    else:
        linesegments.append(uplist)

    display_lines(linesegments, 5)
    retval = pid.wait()   # wait for pid end?

#--------------------------------------------------------------------------
def get_IP2():
    status = wifi.status()
    if "ssid" in status and "ip_address" in status:
        linesegments = [cap("AP:" + status["ssid"], 16)]
        linesegments.append(status["ip_address"])
    else:
        linesegments = ["Not connected", "to wifi."]
    display_lines(linesegments, 3)

#--------------------------------------------------------------------------

def switch_backlight(backlight):
    clear_screen(0.5)

    if backlight:
        turnoff_backlight()
    else:
        turnon_backlight()
    return not backlight

#--------------------------------------------------------------------------
   
def toggle_admin():
    global admin_level

    admin_level = not admin_level
    linesegments = ["admin lvl: "+str(admin_level)]
    display_lines(linesegments, 3)

#--------------------------------------------------------------------------
   
def shutdown(res_type):
    if admin_level:
        if res_type == "shutdown":
            linesegments = ["Shutting down"]
            cmd = 'sudo shutdown now'
        else:
            linesegments = ["Rebooting..."]
            cmd = 'sudo reboot'
        display_lines(linesegments, 3)
        clear_screen(0.1)
        turnoff_backlight()

        pid = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT)
        while True:
            time.sleep(1)
    else:
        linesegments = ["Not allowed"]
        display_lines(linesegments, 3)
        clear_screen(0.5)

#-----------------------------------------------------------------

if (__name__ == "__main__"):
    backlight = True
    print("pax_config.py")

    init_pax()
    keypad = Keypad()

    try:
        while True:
            print("0=Help")
            s = input(">")
            print()

            if s  == "0":
                print("0, 1, 2, 3, 4, 7, 9, q")
            elif s == "1":
                uptime()
            elif s == "2":
                get_IP2()
            elif s == "3":
                pass
            elif s == "4":
                backlight = not backlight
                switch_backlight(backlight)
            elif s == "7":
                toggle_admin()
            elif s == "9":
                shutdown()
            elif s == "q":
                break

    except KeyboardInterrupt:
        print("KeyboardInterrupt")
