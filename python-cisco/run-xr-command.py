from netmiko import Netmiko
import argparse

devices = [{
    "device_type": "cisco_xr",
    "ip": "10.102.156.5",
    "username": "iag",
    "password": "iagpass",
    "port": "22",
}]

parser = argparse.ArgumentParser()
parser.add_argument("--cmd", type=str)
args = parser.parse_args()

for device in devices:
    net_connect = Netmiko(**device)
    output = net_connect.send_command(args.cmd)
    net_connect.disconnect()
    print("---------------Script Ouptut---------------")
    print ("Cmd: " + args.cmd + "\n" + output)
    print("-------------------------------------------")