#! /usr/bin/python3

import select
import subprocess
import sys
import threading
import time

# Own libraries from immediate directory
from paxlib import *
import read_kbd_direct

LAN_IFACE = "wlan0"

io_terminal = True   # use terminal
io_pax      = True   # use keypad, pax display

try:
    import readchar
#   Usage: 
#      char = repr(readchar.readchar())
#      key  = repr(readchar.readkey())
except ImportError:
    print("Module not found: readchar")
    print("Run: sudo pip3 install readchar")
    sys.exit()

class Wifi:
#   Object variables:
#       scroll[]
#       networks{}

    def __init__(self):
        pass
        
    def display(self, myprint="", linesegments=[], delay=0):
        if io_terminal and myprint != "":
            print(myprint)
        if io_pax:
            display_lines(linesegments, delay)

    def getkey(self):
        timeout = 0.1
        while True:
#           key = self.kbd.read_from()
#           if key is not None:
#               return key

            # Try keypad next
            keypad = spin(timeout)
            if keypad[0]:
                key = keypad[1]
                return key

    def wpa_cli(self, cmd, n_id=-1, parm=""):
        # Need full path name: wpa_cli is not in PATH when executed
        # from a @reboot in crontab
        wpa_cli_in = '/usr/sbin/wpa_cli -i' + LAN_IFACE + " " + cmd
        if n_id >= 0:
            wpa_cli_in += " " + str(n_id) + " " + parm
        wpa_cli_in = wpa_cli_in.split()
        self.pid = subprocess.Popen(wpa_cli_in, stdin=subprocess.PIPE, \
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        return self.pid.communicate()[0].decode("utf-8")

    def scan_results(self):
        names = {}
        result = self.wpa_cli("scan_results")
        lines = result.splitlines()[1:]   # separate lines, discard 1st line
        for line in lines:
            ll = line.split()
            if len(ll) >= 5 and ll[4][0:2] != "\\x":  # name can be 0x00-not wanted
                names[ll[4]] = (int(ll[2]), ll[3])
        return names

    def list_networks(self):
        self.networks = {}
        result = self.wpa_cli("list_networks")
        lines = result.splitlines()[1:]   # separate lines, discard 1st line
        for line in lines:
            ll = line.split()
            if ll[1] == "any":
                ll[1] = ""
            self.networks[ll[1]] = int(ll[0])

    def get_network_password(self):
        self.kbd = read_kbd_direct.KDirect()

        e_password = "Enter password: "
        linesegments = [e_password, ""]
        self.display(myprint=e_password, \
                linesegments=linesegments, \
                delay=0)

        line = ""
        while True:
#           key = readchar.readchar()
            key = self.kbd.read_from()
#           print(key.encode().hex(), flush=True)
            if key in ["\r", "\n"]:
                print()
                self.kbd.exit()  # cleanup keyboard routines.
                return line
            if key in ["\x03", "\x1b"]:  # ^C, esc
                print()
                self.kbd.exit()  # cleanup keyboard routines.
                return ""
            if key == "\x7f":
                print("\r" + " " * len(line), end="", flush=True)
                line = line[0:-1]
            else:
                line += key
            print("\r" + line, end="", flush=True)
            linesegments[1] = line
            display_lines(linesegments, 0)


    def add_network(self, nname="", locked=False):
        password = ""
        try:
            print("Enter values, ^C to exit.")
            name = input("New network name: ") if nname == "" else nname
            if locked:
#               password = input("Network password: ")
                password = self.get_network_password()
                if len(password) == 0:
                    return False
        except KeyboardInterrupt:
            print()
            return False
        id = int(self.wpa_cli("add_network"))
        result = self.wpa_cli("set_network", id, parm='ssid "'+name+'"')
        if len(password) == 0:
            result = self.wpa_cli("set_network", id, parm='key_mgmt NONE')
        else:
            result = self.wpa_cli("set_network", id, parm='psk "'+password+'"')
            result = self.wpa_cli("set_network", id, parm='key_mgmt WPA-PSK')
        result = self.wpa_cli("enable_network", id)
        result = self.wpa_cli("save_config")
        return True

    def remove_network(self, ssid=""):
        if ssid == "":
            try:
                print("Enter value, ^C to exit.")
                id = input("Network # to remove: ")
                id = int(id)
            except KeyboardInterrupt:
                print()
                return
            except ValueError:
                print("(ignored)")
                return
        else:
            id = self.networks[ssid]
        result = self.wpa_cli("remove_network", id)
        discard = self.wpa_cli("save_config")
        return result

    def select_network(self, ssid=""):
        if ssid == "":
            try:
                print("Enter value, ^C to exit.")
                id = input("Enter network to use: ")
                id = int(id)
            except KeyboardInterrupt:
                print()
                return
            except ValueError:
                print("(ignored)")
                return
        else:
            try:
                id = self.networks[ssid]
            except KeyError:  # bad -id - typcally: No wifi
                return        # we then check for status
        result = self.wpa_cli("select_network", id)
        time.sleep(1)
        return result

    def reconfigure(self):
        result = self.wpa_cli("reconfigure")
        return result

    def status(self):
        status = {} 
        result = self.wpa_cli("status",)
        for line in result.splitlines():
            ll = line.split("=")
            if ll[0] in ("id", "ssid", "key_mgmt", "ip_address", "wpa_state"):
                status[ll[0]] = ll[1]
        return status

    def get_IP2(self):
        '''Duplicate of function in paxconfig - fix sometime will you?
        '''
        status = wifi.status()
        if "ssid" in status:
            linesegments = [cap("AP:" + status["ssid"], 16)]
            linesegments.append(status["ip_address"])
        else:
            linesegments = ["Not connected", "to wifi."]
        self.display(myprint="", linesegments=linesegments, delay=3)

    def is_locked(self, key_mgmt):
        key_mgmt = key_mgmt.replace("[",'')   # discard "["
        key_mgmt = key_mgmt.split("]")        # split on "]"
        for key in key_mgmt:
            if key[0:3] == "WPA":
                return True
        return False
    
    def sig_strength(self, db):
        if db in range(-20, 0):
            return 4
        if db in range(-70,-21):
            return 3
        if db in range(-80, -71):
            return 2
        return 1

    def build_term_line(self, d):
        locked =  "L" if d["locked"] else " "
        defined = "F" if d["defined"] else " "
        current = "*"  if d["current_ap"] else " "
        return current + locked + d["strength"] + defined + " " + d["ssid"]

    def build_pax_line(self, d):
        locked =  "Lkd " if d["locked"] else "Unl "
        defined = "Dfd " if d["defined"] else "Und "
        current = "AP "  if d["current_ap"] else ""
        return [cap(d["ssid"], 16), "S"+d["strength"] + " " + locked + defined + current]

    def build_scroll(self):
        status = self.status()
        self.list_networks()
        ssids = self.scan_results()
        self.scroll = []
        for ssid in ssids:
            try:
                current_ap = status["ssid"] == ssid and \
                        status["ip_address"][0:7] != "169.254"  # T/F value
            except KeyError: #  not defined - hence it's the "no wifi" case
                current_ap = False
            locked = self.is_locked(ssids[ssid][1])
            strength = str(self.sig_strength(ssids[ssid][0]))
            defined = ssid in self.networks # T/F value
            ssid_info ={"current_ap":current_ap, "locked":locked, "strength":strength,
                        "defined":defined, "ssid":ssid}
            self.scroll.append(ssid_info)
        if len(self.scroll) == 0:   # Add a dummy entry
            self.scroll = [{"current_ap":False, "locked":False,
                    "strength":"0", "defined":False, "ssid":'No wifi'}]

    def wifi_help(self):
        term_help = "(h)elp, (n)ext, (b)efore, (s)elect, (r)emove, " + \
                "(m)anage netwk, (q)uit:"
        pax_help =[ "2=Back AP",
                    "5=Next AP",
                    "3=Select AP",
                    "6=Manage AP",
                    "9=Remove defn",
                    "*=Exit Config" ]
        return term_help, pax_help

    def _change_ap(self, ssid):
        inactive = {"INACTIVE", "INTERFACE_DISABLED", "DISCONNECTED"}

        self.select_network(ssid)
        while True:
            status = self.status()
            print(status)
            if status["wpa_state"] in inactive or \
                    ("ip_address" in status and status["ip_address"][0:7] == "169.254"):
                # Bad pw, addess, or something \
                self.display(myprint="Select failed", \
                        linesegments=["Select failed"], delay=2)
                return
            if "ssid" in status and "ip_address" in status:
                linesegments = [cap("AP:" + status["ssid"], 16)]
                linesegments.append(status["ip_address"])
                self.display(myprint="", linesegments=linesegments, delay=3)
                return
#           ...  expect status["wpa_state"] == "COMPLETED" or "ASSOCIATING":
            self.display(myprint="", \
                    linesegments=["Select pending"], delay=0)
            time.sleep(1)

    def wifi_config(self):
        s_line = 0 
        linesegments=["wifi config>"]
        linesegments.append("0=Help Config")
        self.display(myprint="(h)elp, (n)ext, (b)efore, (s)elect, (r)emove, " + \
                "(m)anage netwk, (q)uit:", \
                linesegments=linesegments, delay=2)

        self.build_scroll()
        while True:
            self.display(myprint=self.build_term_line(self.scroll[s_line]), \
                    linesegments=self.build_pax_line(self.scroll[s_line]), \
                    delay=0)

            key  = self.getkey()
# Help
            if   key in ("0", "h"):
                myprint, linesegments = self.wifi_help()

                self.display(myprint=myprint, \
                        linesegments=linesegments, \
                        delay=3)
# Next
            elif key in ("n", "2", "\r", " "):
                s_line += 1
                if s_line >= len(self.scroll):
                    self.build_scroll()  # rebuild scroll as we rollover
                    s_line = 0           #     to bring in updates
# Back
            elif key in ("b", "5"):
                s_line = s_line - 1 if s_line > 0 else len(self.scroll) - 1
# Select network
            elif key in ("s", "3"):
                ssid   = self.scroll[s_line]["ssid"]
                if not self.scroll[s_line]["defined"]:
                    locked = self.scroll[s_line]["locked"]
                    if self.add_network(ssid, locked):
                        self.list_networks()  # update networks dict
                        self.scroll[s_line]["defined"] = True
                    else:
                        continue

                self._change_ap(ssid)

                self.build_scroll()
                s_line = min(s_line, len(self.scroll)-1)    # in case we see
                                                            # fewer wifi units out there
                                                            # after the build_scroll.
# Remove network from wpa_supplicant.conf
            elif key in ("r", "9"):
                if self.scroll[s_line]["current_ap"]:
                    self.display(myprint="Can't remove active network", \
                            linesegments=["Can't remove", "active network"], delay=2)
                    continue
                ssid = self.scroll[s_line]["ssid"]
                if ssid in self.networks:
                    self.remove_network(self.scroll[s_line]["ssid"])
                    self.scroll[s_line]["defined"] = False
                    self.list_networks()
                else:
                    self.display(myprint="ssid not in definitions", \
                            linesegments=["ssid not in", "definitions"], delay=2)
# Manage networks
            elif key in ("m", "6"):
                ssid = self.scroll[s_line]["ssid"]
                if self.scroll[s_line]["defined"]:
                    password = ""
                    if self.scroll[s_line]["locked"]:
                        try:
#                           password = input("Network password: ")
                            password = self.get_network_password()
                            if len(password) == 0:
                                continue
                        except KeyboardInterrupt:
                            continue
                    id = self.networks[ssid]
                    result = self.wpa_cli("set_network", id, parm='psk "'+password+'"')
                    if len(password) == 0:
                        result = self.wpa_cli\
                                ("set_network", id, parm='key_mgmt NONE')
                    else:
                        result = self.wpa_cli("set_network", id, parm='key_mgmt WPA-PSK')
                    result = self.wpa_cli("save_config")
                elif self.add_network(ssid, \
                            locked=self.scroll[s_line]["locked"]):
                                           # captures password in add_network.
                    self.list_networks()  # update networks dict
                    self.scroll[s_line]["defined"] = True
                else:
                    pass    # not defined and failed add_network (^C) >> ignore
# Quit, Exit
            elif key in ("q", "x", "*"):
                break
# Unrecognized/Repeat
            else:
                self.display(myprint="", linesegments=[], delay=0)


if (__name__ == "__main__"):
    wifi = Wifi()

    try:
        while True:
#           keypad.wait_keypress()
#           print(keypad.key,  keypad.cseconds, keypad.keytype)
            cli = input('scan, list_n, add, remove, select, status, ' +
                        'reconfigure, all, w/config, quit: ').strip()
            if len(cli) == 0:
                continue
            elif cli == "scan"[0:len(cli)]:
                ssids = wifi.scan_results()
                print(ssids)
            elif cli == "list_n"[0:len(cli)]:
                wifi.list_networks()
                print(wifi.networks)
            elif cli == "add"[0:len(cli)]:
                result = wifi.add_network()
                print(result)
                wifi.list_networks()
                print(wifi.networks)
            elif cli == "remove"[0:len(cli)]:
                result = wifi.remove_network()
                print(result)
                wifi.list_networks()
                print(wifi.networks)
            elif cli == "select"[0:len(cli)]:
                result = wifi.select_network()
                print(result)
                status = wifi.status()
                print(status)
            elif cli == "status"[0:len(cli)]:
                status = wifi.status()
                print(status)
            elif cli == "reconfigure"[0:len(cli)]:
                result = wifi.reconfigure()
                print(result)
                wifi.list_networks()
                print(wifi.networks)
            elif cli == "all"[0:len(cli)]:
                wifi.build_scroll()
                for line in wifi.scroll:
                    print(line["line"])
            elif cli == "w/config"[0:len(cli)]:
                wifi.wifi_config()
            elif cli == "quit"[0:len(cli)]:
                break
            
    except KeyboardInterrupt:
        print()
