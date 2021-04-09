#! /usr/bin/python3
'''
See: /usr/local/lib/python3.7/dist-packages/evdev/ecodes.py

Keys are defined here:
/usr/include/linux/input-event-codes.h

'''

import evdev
import threading
import sys
import time

class KDirect():
    shift = False
    ctrl  = False
    shift_keys = {'KEYS_CAPSLOCK': False}   # create shift_keys; other keys added as they come
    
    def __init__(self):
        self.keyboard = self._find_keyboard()
        if self.keyboard is None:
            return
        self._grab_keyboard()   # My keyboard, plus stops local echo.

        # Start flashing routine to flash Caps Lock led.
        self.flash = threading.Thread(target=self._flash_ctl)
        self.flash.start()

    def _find_keyboard(self):
        for _ in range(0, 2):       # try a couple of times to find a keyboard
            devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
            for device in devices:
#               print(device.path, device.name, device.phys)
                if "keyboard" in device.name.lower() and \
                        "control" not in device.name.lower():
                    print("Using", device.path, device.name)
                    return device
            time.sleep(0.5) # pause before we scan again
        return None

    def _grab_keyboard(self):
        try:
            self.keyboard.grab()   # My keyboard! Mine I say!
        except OSError:
            print("Someone else has the keyboard! Exiting!")
            sys.exit()

    def read_from(self):
        while True:
            try:
                for event in self.keyboard.read_loop():
                    if event.type == evdev.ecodes.EV_KEY:
                        result = self._handle(event)
                        if result is None:
                            continue
                        return result

            except OSError:          # we have lost the keyboard
#           except AttributeError:   # we have lost the keyboard
                del self.keyboard   # device has gone, destroy it so flash can't use it.
                self.keyboard = self._find_keyboard()  # ... and rebuild it
                self._grab_keyboard()

    def _handle(self, event):
        # see values: /usr/local/lib/python3.7/dist-packages/
        #              evdev/events.py
        # Constants
        key_up = evdev.events.KeyEvent.key_up
        key_down = evdev.events.KeyEvent.key_down
        key_hold = evdev.events.KeyEvent.key_hold

        shift_set = {'KEY_LEFTSHIFT','KEY_RIGHTSHIFT',
                     'KEY_LEFTCTRL', 'KEY_RIGHTCTRL', 'KEY_CAPSLOCK'}
        char = {'GRAVE': ('`', '~'), 'MINUS': ('-', '_'), 'EQUAL': ('=', '+'),
                'LEFTBRACE': ('[', '{'), 'RIGHTBRACE': (']','}'), 'BACKSLASH': ('\\', '|'),
                'SEMICOLON': (';', ':'), 'APOSTROPHE': ("'", '"'), 'COMMA': (',', '<'),
                'DOT': ('.','>'), 'SLASH': ('/', '?'),
                '1': ('1', '!'), '2': ("2", '@'), '3': ('3' '#'), '4': ('4', '$'),
                '5': ('5', '%'), '6': ("6", '^'), '7': ('7' '&'), '8': ('8', '*'),
                '9': ('9', '('), '0': ('0' ')') }
        spec_char = {'BACKSPACE': '\x7f', 'ESC': '\x1b',
                     'SPACE': ' ', 'ENTER': '\n', 'ctl_c': '\x03'}

#       print(evdev.categorize(event))
#       print(event.type, event.code, event.value)
        key = evdev.ecodes.KEY[event.code]
#       print(key)
        if event.value == key_hold:
            return       # ignore
        
        if key in shift_set:
#           print(key)
            self._shift_key(key, event.value==key_down)
            return
        if event.value == key_up:
            return       # ignore
        # We have a real key press
#       print(key)
        symbol = key[4:]    # trim off "KEY_"

        if self.ctrl and symbol == "C":   # ^C
            return spec_char["ctl_c"]
        if self.ctrl and symbol == "LEFTBRACE":   # manual esc
            return spec_char["ESC"]

        if len(symbol) == 1 and symbol not in "0123456789":  # then a letter key
            return symbol if self.shift else symbol.lower()  # symbol is retrieved
                                                             #     as uppercase
        if symbol in char:   # 
            shift = 1 if self.shift else 0
            return char[symbol][shift]

        if symbol in spec_char:
                return spec_char[symbol]

        return    # with None, and look for next input

    def _shift_key(self, key, key_down):
#       print(key)
        if key_down and key == "KEY_CAPSLOCK":
            self.shift_keys['KEYS_CAPSLOCK'] = \
                    not self.shift_keys['KEYS_CAPSLOCK'] 
        else:
            self.shift_keys[key] = key_down   # True or False

        self.shift = self.shift_keys['KEYS_CAPSLOCK']

#       print(shift_keys)
        for a_key in self.shift_keys: # search for any shift key that's down
            if a_key[-5:] == 'SHIFT' and self.shift_keys[a_key]:
                self.shift = True
                break

        if self.shift:    # turn on capslock led
            self._set_led(True)
            self.flash_pause = True
        else:
            self.flash_pause = False   # No shift keys on;
                                       # ...will force set_led to start flashing.

        self.ctrl = False
        for a_key in self.shift_keys: # if any shift key is down
            if a_key[-4:] == 'CTRL' and self.shift_keys[a_key]:
                self.ctrl = True     # find a ctrl key that is True
                break

#-----------------------------------------------------------------------------
    def _set_led(self, shine):
    #   set led
        while True:
            try:
                dev =self.keyboard    # the device - it should work fine
                break
#           except OSError:         # but if the device disappears (not defined)
            except AttributeError:  # but if the device disappears (not defined)
                time.sleep(2)         # ... then try again soon.
        dev.set_led(evdev.ecodes.LED_CAPSL, shine)
        return

#-----------------------------------------------------------------------------
    flashing = True   
    flash_pause = False
    def _flash_ctl(self):
        shine = True
        while self.flashing:
            time.sleep(1)
            while self.flash_pause:
                time.sleep(0.1)
            self._set_led(shine)
            shine = not shine
        self._set_led(False)

#-----------------------------------------------------------------------------
    def exit(self):
        self.keyboard.ungrab()
        self.flash_pause = False
        self.flashing = False
        self.flash.join()

#-----------------------------------------------------------------------------
if __name__ == "__main__":        
    kbd = KDirect()
    while True:
        try:
            key = kbd.read_from()
            if key == '\n':
                break
            print(key, end="", flush=True)
        except KeyboardInterrupt:
            break

    kbd.exit()
    print("")
