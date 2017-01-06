#! /usr/bin/python3

import time
import sys
import subprocess
from paxlib import *
#from keypadlib import *

#-----------------------------------------------------------------
def config_help():
    '''show config commands'''
    linesegments = []
    linesegments.append("1=Show Uptime")
    linesegments.append("2=Show my IP")
    linesegments.append("3=Show my AP")
    linesegments.append("6=Show all APs")
    linesegments.append("4=Sw. backlight")
    linesegments.append("7=w/ls conf help")
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
        linesegments.append("0=Help Config")
        linesegments.append("config>")
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
            get_IP(maxcount=5)
        elif keyvalue == "3":             # Show my wireless AP name.
            get_AP()
        elif keyvalue == "4":             # Switch backlight
            pax_2x16_backlight= switch_backlight(pax_2x16_backlight) # True = On
        elif keyvalue == "6":             # Show wireless.
            show_wireless()
        elif keyvalue == "7":             # Give help for mobile device wireless config
            give_mobile_help()
        elif keyvalue == "9":             # Shutdown (poweroff)
            shutdown()
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

def get_AP():
    ''' get my accesspoint name'''
    linesegments = []
    linesegments.append("My AP:")

    a_point = 'iwconfig wlan0'
#   example: wlan0     IEEE 802.11bgn  ESSID:"Hollywood29"

    pid = subprocess.Popen(a_point, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    s_stdout = pid.stdout.readlines()   # appears we can only call this one time
    s_stdout = s_stdout[0]              # Get single list entry of a byte string
    s_stdout = s_stdout.decode("utf-8").strip()   # Convert to a string & trim

#   print(s_stdout)
    essid = s_stdout.split()
    if len(essid) >= 4:
        ap = essid[3][7:-1]
    else:
        ap = "(Not found)"

#   print(ap)
    linesegments.append(cap(ap, 16))
    display_lines(linesegments, 5)

#--------------------------------------------------------------------------

def get_IP(maxcount=10):
    title = "My IP"
    for i in range(0, maxcount):
        myhost = '/bin/hostname -I'

        pid = subprocess.Popen(myhost, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        title += ":"

        init_screen(0.5)                     # repeated here in case/when the init fails elesewhere
        linesegments = [title]

#       for line in pid.stdout.readlines():
#       Only 1 line returned.
#       It may be: empty, have 1 IP address, multiple IP addresses separated by wh space.
        line = pid.stdout.readlines()[0]   # Lines is a list - get only 1st line
        line = line.decode("utf-8").strip() #convert to string, strip off trailing whitespace " \n"

#       print("hostname -I:" + line)
#       print("len hostname line=", len(line))

        if len(line) == 0:
            pass
        else:
#       Assume 1, more IP addresses as words.
            ip_addresses = line.split()
            for ip in ip_addresses:
                linesegments.append(">" + ip)

#       print(linesegments)
        display_lines(linesegments, 2)
        retval = pid.wait()   # not sure what this does - waits for pid end?

        if len(linesegments[1]) > 2:
            return

        if spin(1):   # if the keypad gets touched, then we've finished.
            return

#--------------------------------------------------------------------------

def show_wireless():
#   iwlist wlan0 scan | grep -e Cell -e ESSID -e Encrypt -e Quality
#  ['A-Points:',
    ''' Typical output from iwlist:
'Cell 01 - Address: 28:C6:8E:B5:2', 'Quality=31/70  Signal level=-79 ', 'Encryption key:on', 'ESSID:"HRETMRP6"',
    '''
    accesspoints = []

    linesegments = []
    linesegments.append("Get access-")
    linesegments.append("points:")
    display_lines(linesegments, 0)

    a_points = 'iwlist wlan0 scan | grep -e Cell -e ESSID -e Encrypt -e Quality'

    pid = subprocess.Popen(a_points, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    ap_count = 0
    for line in pid.stdout.readlines():
        ap_line = line.decode("utf-8").strip()
                                         #convert to string, strip off start/trailing whitespace
        if ap_line[0:4] == "Cell":
            accesspoints.append({})
            accesspoints[-1]["Cell"] = ap_line[5:7]
        elif ap_line[0:7] == "Quality":
            accesspoints[-1]["Quality"] = ap_line[-7:-4]
        elif ap_line[0:7] == "Encrypt":
            accesspoints[-1]["Encrypt"] = ap_line[-2:] if ap_line[-1] == "n" else ap_line[-3:] 
        elif ap_line[0:5] == "ESSID":
            accesspoints[-1]["ESSID"] = ap_line[7:-1]
        
    accesspoints = sort_ap(accesspoints)   # sort in order of quality - highest first

    linesegments = []
    for entry in accesspoints:
#       print(entry["Cell"])
        linesegments.append(cap(entry["Cell"] + " " + entry["ESSID"], 16))
        linesegments.append(entry["Quality"] + " Encr:" + entry["Encrypt"])

#   print(accesspoints)
    display_lines(linesegments, 3)
    retval = pid.wait()   # not sure what this does - waits for pid end?
    time.sleep(1)   # wait a bit of extra time.

#   Ignore key press value - wrong... want it!

def ap_key(item):
    return item["Quality"]

def sort_ap(accesspoints):
    return sorted(accesspoints, key=ap_key)   # key is the sort key for the list element

#--------------------------------------------------------------------------

def switch_backlight(backlight):
    clear_screen(0.5)

    if backlight:
        turnoff_backlight()
    else:
        turnon_backlight()
    return not backlight

#--------------------------------------------------------------------------
   
def give_mobile_help():
    linesegments = [
    #     12345678901234567890
         "1 Att. USB cable",
         "2 Ph:Set Tetherg",
         "3--ass. running:",
         "  tightvncserver",
         "4 Ph:VNC to:",
         " 192.168.42.42:1",
         "5 RPi screen:",
         " set AP & pwd",
         " ",
         " ",
         "tightvncserver:",
         "1 Ph:VxConnectBO",
         "2 Vx:login pi/g*",
         "3 >tightvncserv*",
         "4 Disconnect"
        ]
    display_lines(linesegments, 4)
    pass

#--------------------------------------------------------------------------
   
def shutdown():
    allow_shutdown = False

    linesegments = ["Shutting down"]
    display_lines(linesegments, 3)

    clear_screen(0.1)
    turnoff_backlight()
    clear_screen(1)

    if allow_shutdown:
        cmd = 'sudo shutdown now'
        pid = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT)
        #   NEW CODE: ASK FOR PASSWORD
        #   We should die, but let's see what happens
        while True:
            time.sleep(1)
    else:
        turnon_backlight()
        clear_screen(0.1)

        linesegments = ["Not allowed"]
        display_lines(linesegments, 3)

        clear_screen(0.5)

#-----------------------------------------------------------------

if (__name__ == "__main__"):
    print("pax_config.py")

    init_pax()
    keypad = Keypad()

    try:
        while True:
            print("0=Help")
            s = input(">")
            print()

            if s  == "0":
                print("0, 1, 2, q")
            elif s == "1":
                get_IP(10)
            elif s == "2":
                show_wireless()
            elif s == "q":
                break

    except KeyboardInterrupt:
        print("KeyboardInterrupt")
