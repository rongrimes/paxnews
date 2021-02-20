#! /usr/bin/python3

import subprocess
import sys
import time

LAN_IFACE = "wlan0"
key_type = {"none":"none", "singlekey":"single key", "long":"Long", "double":"Double"}

import termios  # for devp
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
#Methods:
#  pressed:
#    Returns True if a key is pressed (& released). Key value in self.key
#    Returns False python if a key is not pressed/released.
#

    key_val ={ "up", "down", "define", "select", "remove", "password", "exit" }

    def __init__(self):
        pass
        
    def read_pad(self):        
        pass

    def wpa_cli(self, cmd, n_id=-1, parm=""):
        wpa_cli_in = 'wpa_cli -i' + LAN_IFACE + " " + cmd
        if n_id >= 0:
            wpa_cli_in += " " + str(n_id) + " " + parm
        wpa_cli_in = wpa_cli_in.split()
        self.pid = subprocess.Popen(wpa_cli_in, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        return self.pid.communicate()[0].decode("utf-8")

    def scan_results(self):
        names = {}
        result = self.wpa_cli("scan_results")
        lines = result.splitlines()[1:]   # separate lines, discard 1st line
        for line in lines:
            ll = line.split()
#           if len(ll) >= 5 and "x" in ll[4]:  # name can be \0x0000... - not wanted
#               print(ll[4])
            if len(ll) >= 5 and ll[4][0:2] != "\\x":  # name can be 0x0000
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

    def add_network(self, nname=""):
        try:
            print("Enter values, ^C to exit.")
            name = input("New network name: ") if nname == "" else nname
            password = input("Network password: ")
        except KeyboardInterrupt:
            return
        id = int(self.wpa_cli("add_network"))
        result = self.wpa_cli("set_network", id, parm='ssid "'+name+'"')
        result = self.wpa_cli("set_network", id, parm='psk "'+password+'"')
        result = self.wpa_cli("set_network", id, parm='key_mgmt WPA-PSK')
        result = self.wpa_cli("enable_network", id)
        result = self.wpa_cli("save_config")
        return result

    def remove_network(self, ssid=""):
        if ssid == "":
            try:
                print("Enter value, ^C to exit.")
                id = input("Network # to remove: ")
                id = int(id)
            except KeyboardInterrupt:
                return
            except ValueError:
                print("(ignored)")
                return
        else:
            id = self.networks[ssid]
        result = self.wpa_cli("remove_network", id)
        discard = self.wpa_cli("save_config")
        return result

    def select_network(self):
        try:
            print("Enter value, ^C to exit.")
            id = input("Enter network to use: ")
            id = int(id)
        except KeyboardInterrupt:
            return
        except ValueError:
            print("(ignored)")
            return
        result = self.wpa_cli("select_network", id)
        time.sleep(5)
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

    def show_ssid(self, current_ap, ssid, locked, strength, defined):
        print(current_ap + locked + strength + defined, ssid)
        
    def is_locked(self, key_mgmt):
        key_mgmt = key_mgmt.replace("[",'')   # discard "["
        key_mgmt = key_mgmt.split("]")        # split on "]"
        for key in key_mgmt:
            if key[0:3] == "WPA":
                return "L"
        return " "
    
    def sig_strength(self, db):
        if db in range(-20, 0):
            return 4
        if db in range(-70,-21):
            return 3
        if db in range(-80, -71):
            return 2
        return 1

    def build_line(self,d):
        return d["current_ap"] + d["locked"] + d["strength"] + d["defined"] + " " + d["ssid"]  

    def build_scroll(self):
        status = wifi.status()
        wifi.list_networks()
        ssids = wifi.scan_results()
        wifi.scroll = []
        for ssid in ssids:
            current_ap = "*" if "ssid" in status and \
                                status["ssid"] == ssid else " "
            locked = wifi.is_locked(ssids[ssid][1])
            strength = str(wifi.sig_strength(ssids[ssid][0]))
            defined = "D" if ssid in wifi.networks else " "
            ssid_info ={"current_ap":current_ap, "locked":locked, "strength":strength,
                        "defined":defined, "ssid":ssid}
            ssid_info["line"] = self.build_line(ssid_info)
            wifi.scroll.append(ssid_info)

    def getkey(self):
        kbd = True
        if kbd:
            return readchar.readchar()
        else:
            # get input from keypad > TBD
            pass
        return key

    def choose(self):
        s_line = 0 
        
        while True:
            print(wifi.scroll[s_line]["line"] + " ", end="", flush=True)
            key  = wifi.getkey()

            if   key in ("u", "1"):  # Up 
                print()
                s_line += 1
                if s_line >= len(wifi.scroll):
                    s_line = 0
            elif key in ("d", "4", "\r", " "):  # Down
                print()
                s_line = s_line - 1 if s_line > 0 else len(wifi.scroll) - 1
            elif key in ("f", "2"):  # deFine
                print("f")
                wifi.add_network(wifi.scroll[s_line]["ssid"])
                wifi.scroll[s_line]["defined"] = "D"
                wifi.scroll[s_line]["line"] = self.build_line(wifi.scroll[s_line])
            elif key in ("s", "3"):  # Select
                print("s")
            elif key in ("r", "6"):  # Remove
                print("r")
                wifi.remove_network(wifi.scroll[s_line]["ssid"])
                wifi.scroll[s_line]["defined"] = " "
                wifi.scroll[s_line]["line"] = self.build_line(wifi.scroll[s_line])
            elif key in ("p", "5"):  # Password
                print("p")
            elif key in ("q", "x", "*"):  # Quit, eXit
                print()
                return
            else:
                print()


'''
        # get my accesspoint name
#       linesegments = []
#       linesegments.append("My AP:")

#       linesegments.append(cap(ap, 16))
#       display_lines(linesegments, 5)
'''


if (__name__ == "__main__"):
    wifi = Wifi()

    try:
        while True:
#           keypad.wait_keypress()
#           print(keypad.key,  keypad.cseconds, keypad.keytype)
            cli = input('scan, list_n, add, remove, select, status, ' +
                        'reconfigure, all, choose*, quit: ').strip()
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
            elif cli == "choose"[0:len(cli)]:
                wifi.build_scroll()
                wifi.choose()
            elif cli == "quit"[0:len(cli)]:
                break
            
    except KeyboardInterrupt:
        print()
