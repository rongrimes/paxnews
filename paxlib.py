#!/usr/bin/python3

import serial
import sys
import time

# Own libraries from immediate directory
from keypadlib import *

#-----------------------------------------------------------------
#Global assignments

pax = {
    'LcdBkSpc': b'\x08',  	# move cursor left
    'LcdRt':    b'\x09',  	# move cursor right
    'LcdLF':    b'\x0A',  	# move cursor down 1 line
    'LcdCls':   b'\x0C',  	# clear LCD (need 5 ms delay)
    'LcdCR':    b'\x0D',  	# move pos 0 of next line
    'LcdBLon':  b'\x11',  	# backlight on
    'LcdBLoff': b'\x12',  	# backlight off
    'LcdOff':   b'\x15',  	# LCD off
    'LcdOn1':   b'\x16',  	# LCD on; no crsr, no blink
    'LcdOn2':   b'\x17',  	# LCD on; no crsr, blink on
    'LcdOn3':   b'\x18',  	# LCD on; crsr on, no blink
    'LcdOn4':   b'\x19',  	# LCD on; crsr on, blink on
    'LcdLine1': b'\x80',  	# move to line 1, column 0
    'LcdLine2': b'\x94'   	# move to line 2, column 0
}

pax_2x16_backlight = True

#-----------------------------------------------------------------
def init_pax():
    global pax_2x16
    global keypad
    global pax_2x16_backlight

#   print('init_pax')
    # Open Serial port
    try:
        pax_2x16 = serial.Serial(
#                  port='/dev/ttyAMA0',
                   port='/dev/ttyS0',
                   baudrate = 19200,
                   parity=serial.PARITY_NONE,
                   stopbits=serial.STOPBITS_ONE,
                   bytesize=serial.EIGHTBITS,
                   timeout=1
                   )
    except serial.serialutil.SerialException:
        print("SerialException error: serial port to Parallax display not available.")
        print()
        print("To fix: edit /boot/cmdline.txt")
        print("\tRemove 'console=serial0,xxxxx', and reboot.")
        print()
        print("Alternative:")
        print("\t1. run 'sudo raspi-config'")
        print("\t2. >5. Interfacing Options")
        print("\t3. >P6. Serial")
        print("\t4. ...login shell... over serial? Answer: No")
        print("\t5. ...serial port... enabled?     Answer: Yes")
        print("\t6. Reboot for change to take effect.")
        print()
        sys.exit()

    init_screen(0.5)    # Backlight, cursor off, clear.

    keypad = Keypad()

    return pax_2x16 

#-----------------------------------------------------------------
def display_lines(linesegments, delay, width=16):
    '''Main display utility for the 2x16.
    width is the display width and needs to be 16 or 32.
    '''
    global pax_2x16
    global pax_2x16_backlight
    global keypad

#   Assert code here for width to be: 16, 32
    assert width == 16 or width == 32

#   Add a line if linecount is uneven
    if width == 16 and len(linesegments) % 2 == 1:
        linesegments.append(" ")

    i = 0
    while i < len(linesegments):
        pax_2x16.write(pax["LcdCls"])                # Clear Screen
        if len(linesegments[i]) < width:
            linesegments[i] += "\r"
        pax_2x16.write(bytearray(linesegments[i], "utf-8"))   # Write lines of message

        if width == 16:
            pax_2x16.write(bytearray(linesegments[i+1], "utf-8"))
            i += 2
        else:
            i += 1

        if spin(delay):
            break

#key_type = {"none":"none", "singlekey":"single key", "long":"Long", "double":"Double"}
    return keypad.keytype, keypad.key             # keytype = "None" if not assigned o/wise

#-----------------------------------------------------------------
def init_screen(delay):
    '''initialise screen & wait "delay" seconds'''
    global pax_2x16
    global pax_2x16_backlight

    # Clear screen
    pax_2x16.write(pax["LcdCls"])

    # Turn On Back light
    turnon_backlight()

    # Turn Off cursor
    pax_2x16.write(pax["LcdOn1"])

#   sleep & ignore key press.
    time.sleep(delay)

def clear_screen(delay):
    global pax_2x16
    global pax_2x16_backlight

    '''clear screen & wait "delay" seconds'''
    pax_2x16.write(pax["LcdCls"])     # Clear Screen

#   sleep & ignore key press.
    time.sleep(delay)

def turnoff_backlight():
    global pax_2x16
    global pax_2x16_backlight

    '''Turn off backlight'''
    pax_2x16.write(pax["LcdBLoff"])     # Backlight off
    pax_2x16_backlight = False

def turnon_backlight():
    global pax_2x16
    global pax_2x16_backlight

    '''Turn on backlight'''
    pax_2x16.write(pax["LcdBLon"])     # Backlight off
    pax_2x16_backlight = True

#-----------------------------------------------------------------
# UTILITIES
def cap(s, leng):
    '''Returns s up to a max length of leng'''
    return s if len(s)<=leng else s[0:leng]

def spin(seconds):
    global keypad
    '''Wait the given number of seconds or until a key is pressed.
       Return: True if keypressed; False otherwise.
    '''
    # Work in units of cseconds (1/100 seconds)
    for i in range(0, int(seconds*100)):
        if keypad.pressed():
            return True
        time.sleep(0.01)
    return False

def wait_key():
    global keypad
    '''Wait indefinitely for a key to be pressed.
       Return: keyvalue
    '''
    keypad.wait_keypress()
    return keypad.key

    pass

#-----------------------------------------------------------------

if (__name__ == "__main__"):
    try:
        while True:
            print("paxlib.py")
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
