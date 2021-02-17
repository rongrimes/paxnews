#! /usr/bin/python3

import subprocess
import sys
import time

LAN_IFACE = "wlan0"
key_type = {"none":"none", "singlekey":"single key", "long":"Long", "double":"Double"}

class Wifi:
#Methods:
#  pressed:
#    Returns True if a key is pressed (& released). Key value in self.key
#    Returns False python if a key is not pressed/released.
#

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
        names = []
        result = self.wpa_cli("scan_results")
        lines = result.splitlines()[1:]   # separate lines, discard 1st line
        for line in lines:
            ll = line.split()
            if len(ll) >= 5 and ll[4][0] != 0x00:  # name can be 0x0000... - not wanted
                names.append(ll[4])
#       print(names, "\n")
        return names

    def list_networks(self):
        names = []
        result = self.wpa_cli("list_networks")
        lines = result.splitlines()[1:]   # separate lines, discard 1st line
        for line in lines:
            ll = line.split()
            if ll[1] == "any":
                ll[1] = ""
            names.append((ll[0], ll[1]))
#       print(names, "\n")
        return names

    def add_network(self):
        try:
            print("Enter values, ^C to exit.")
            name =     input("New network name: ")
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

    def remove_network(self):
        try:
            print("Enter value, ^C to exit.")
            id = input("Network to remove: ")
            id = int(id)
        except KeyboardInterrupt:
            return
        result = self.wpa_cli("remove_network", id)
        return result

    def select_network(self):
        try:
            print("Enter value, ^C to exit.")
            id = input("Enter network to use: ")
            id = int(id)
        except KeyboardInterrupt:
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
            if ll[0] in ("id", "ssid", "key_mgmt", "ip_address"):
                status[ll[0]] = ll[1]
                
        return status

'''     while True:
            s_stdout = pid.stdout.readlines()   # appears we can only call this one time
            s_stdout = s_stdout.decode("utf-8").strip()   # Convert to a string & trim

            print(s_stdout)

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
            cli = input('scan, list_n, add, remove, select*, status, reconfigure: ')

            if cli == "scan"[0:len(cli)]:
                ssids = wifi.scan_results()
                print(ssids)
            elif cli == "list"[0:len(cli)]:
                networks = wifi.list_networks()
                print(networks)
            elif cli == "add"[0:len(cli)]:
                result = wifi.add_network()
                print(result)
                networks = wifi.list_networks()
                print(networks)
            elif cli == "remove"[0:len(cli)]:
                result = wifi.remove_network()
                print(result)
                networks = wifi.list_networks()
                print(networks)
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
                networks = wifi.list_networks()
                print(networks)
            
    except KeyboardInterrupt:
#       print()
#       print("KeyboardInterrupt")
        pass
