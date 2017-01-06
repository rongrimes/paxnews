#! /usr/bin/python3

import RPi.GPIO as GPIO
import time
import sys

# row   Pad Pin   Pi Pin
#      (top view)
#      (frm left)
# 0     2          24
# 1     7          21
# 2     6          20
# 3     4          12
#
# col  Pad Pin (top view)
# 0     3          25
# 1     1          23
# 2     5          16

# Fixed: Pad pin
# Varies: Pi Pin

rows = [24, 21, 20, 12]
cols = [25, 23, 16]

keys = [
    ['1', '2', '3'],
    ['4', '5', '6'],
    ['7', '8', '9'],
    ['*', '0', '#']]

key_type = {"none":"none", "singlekey":"single key", "long":"Long", "double":"Double"}

class Keypad:
#Methods:
#  pressed:
#    Returns True if a key is pressed (& released). Key value in self.key
#    Returns False if a key is not pressed/released.
#
#  doublekey:
#    Waits for a key. Returns True if a key is doubly pressed in a short time.
#    key value in self.key
#
#  wait_keypress:
#    Waits until a key is pressed,  & returns it in self.key.
#
#Attributes:
#  key: key value, as a single char string.
#
#  keytype: [none, singlekey, long, double]
#  cseconds: time key was pressed in centi seconds. Not useful outside?

    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        try:
            for row_pin in rows:
                GPIO.setup(row_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        except:
            print("Use sudo to run the program.")
            sys.exit()

        for col_pin in cols:
            GPIO.setup(col_pin, GPIO.OUT)

    def read_pad(self):
        self.key = 0
        self.keytype = key_type["none"]
        self.cseconds = 0   # time unit = cs (centiseconds)
        for col_num, col_pin in enumerate(cols):
            GPIO.output(col_pin, GPIO.HIGH)
            for row_num, row_pin in enumerate(rows):
                if GPIO.input(row_pin):
# Capture the key
                    self.key = keys[row_num][col_num]
                    self.keytype = key_type["singlekey"]
# Check for long press:
                    while GPIO.input(row_pin):
                        time.sleep(0.01)
                        self.cseconds +=1
                        if self.cseconds > 50:
                            self.keytype = key_type["long"]

                    GPIO.output(col_pin, GPIO.LOW)
                    return True
            GPIO.output(col_pin, GPIO.LOW)
        return False

    def pressed(self):
        return self.read_pad()

    def doublekey(self):
# return key & double
        cs_counter = 0
        self.keytype = key_type["double"]

# Get next key if it's there.
        while not self.read_pad():
            time.sleep(0.05)

        hold_key = (self.key, self.cseconds, self.keytype)
        if self.cseconds < 25:  # got one,n < 1/4 s, now see if there's another.
            while not self.read_pad():
                time.sleep(0.01)
                cs_counter += 1
                if cs_counter > 20:  # nothing in 20 cs (.2 s)
                    self.key, self.cseconds, self.keytype = hold_key
                    return False
            if self.cseconds < 25:
                self.keytype = key_type["double"]
                return True
#       Otherwise, return most first key attributes.
        self.key, self.cseconds, self.keytype = hold_key
        return False 
            

    def wait_keypress(self):
        while not self.read_pad():
            time.sleep(0.05)

# want single attribute of: [singlekey, long, double].


if (__name__ == "__main__"):
    keypad = Keypad()

    try:
        while True:
#           keypad.wait_keypress()
            keypad.doublekey()
            print(keypad.key,  keypad.cseconds, keypad.keytype)

    except KeyboardInterrupt:
        print("KeyboardInterrupt")
        GPIO.cleanup()   # Clear any current status
