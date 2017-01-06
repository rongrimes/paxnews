#!/usr/bin/python3

import datetime
import string
import sys
import time
from wifi import Cell, Scheme

#-----------------------------------------------------------------
# Principal loop

cell = Cell.all('wlan0')
# ssid signal quality frequency bitrates encrypted channel address mode encryption_type

for c in cell:
#   print(c.ssid, c.signal, c.quality, c.frequency, c.bitrates, c.encrypted, c.channel, c.address, c.mode, c.encryption_type ) 
    print(c.ssid, c.signal, c.encrypted, c.encryption_type ) 

try:
    while True:
        try:
            getcell = input("Enter wifi name to connect to (starting letters): ")
        except EOFError:
            print("\nGoodbye")
            break
        if len(getcell) == 0:
            continue
        c = Cell.where("wlan0", lambda x: x.ssid.startswith(getcell))
        if len(c) > 0:
            print(c[0].ssid, c[0].signal, c[0].encrypted, c[0].encryption_type ) 
        else:
            print("Not found")
            continue
#       print(c[0].ssid) 
#       scheme = Scheme.for_cell('wlan0', 'Hollywood29', c[0], passkey='FROGS ARE COOL')
        scheme = Scheme.for_cell('wlan0', 'AndroidAP', c[0])
#       scheme.save()
        scheme.activate()

except KeyboardInterrupt:
    print("\rKeyboardInterrupt")

finally:
    pass

