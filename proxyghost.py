#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import getopt
import requests
import time
import re
import signal
import json
import packaging.version
from stem import Signal
from stem.control import Controller
from packaging import version

# Constants
VERSION = "1.0.0"
IP_API = "https://api.ipify.org/?format=json"

LATEST_RELEASE_API = "https://github.com/RoggersOgao/proxyGhost.git"

proxy_url_pattern = re.compile(r"^socks5://[a-zA-Z0-9]+:[a-zA-Z0-9]+@[a-zA-Z0-9.-]+:\d+$")


while True:
    PROXY_URL = input("Enter the proxy URL (format: socks5://username:password@proxy_ip:proxy_port): ")
    if proxy_url_pattern.match(PROXY_URL):
        break
    else:
        print("Invalid proxy URL format. Please try again.")


# Color codes
bcolors = {
    "BLUE": '\033[94m',
    "GREEN": '\033[92m',
    "RED": '\033[31m',
    "YELLOW": '\033[93m',
    "FAIL": '\033[91m',
    "ENDC": '\033[0m',
    "BOLD": '\033[1m',
    "WHITE": '\033[37m'
}

# Function to get current time
def t():
    return time.strftime('%H:%M:%S', time.localtime())

# Function to print logo
def print_logo():
    print(bcolors["GREEN"] + bcolors["BOLD"])
    print(r"""
            /$$$$$$$                                        /$$$$$$  /$$                            /$$
           | $$__  $$                                      /$$__  $$| $$                           | $$
           | $$  \ $$/$$$$$$  /$$$$$$  /$$   /$$ /$$   /$$| $$  \__/| $$$$$$$   /$$$$$$   /$$$$$$$/$$$$$$
           | $$$$$$$/$$__  $$/$$__  $$|  $$ /$$/| $$  | $$| $$ /$$$$| $$__  $$ /$$__  $$ /$$_____/_  $$_/
           | $$____/ $$  \__/ $$  \ $$ \  $$$$/ | $$  | $$| $$|_  $$| $$  \ $$| $$  \ $$|  $$$$$$  | $$
           | $$    | $$     | $$  | $$  >$$  $$ | $$  | $$| $$  \ $$| $$  | $$| $$  | $$ \____  $$ | $$ /$$
           | $$    | $$     |  $$$$$$/ /$$/\  $$|  $$$$$$$|  $$$$$$/| $$  | $$|  $$$$$$/ /$$$$$$$/ |  $$$$/
           |__/    |__/      \______/ |__/  \__/ \____  $$ \______/ |__/  |__/ \______/ |_______/   \___/
                                                 /$$  | $$
                                                |  $$$$$$/
                                                 \______/
        {V} - Roggers Ogao
    """.format(V=VERSION))
    print(bcolors["ENDC"])

# Function to print usage
def usage():
    print_logo()
    print("""
    ProxyGhost Command-Line Options
    =============================

    +-------+----------+---------------------------------------+
    |  Flag  |  Option  |                Description            |
    +-------+----------+---------------------------------------+
    |  -s    | --start  |         Start ProxyGhost              |
    |  -x    | --stop   |         Stop ProxyGhost               |
    |  -h    | --help   |  Print this help and exit             |
    |  -u    | --update |  Check for update                     |
    +-------+----------+---------------------------------------+
    """)
    sys.exit()

# Function to handle SIGINT signal
def sigint_handler(signum, frame):
    print(f"{bcolors['RED']}{time.strftime('%H:%M:%S', time.localtime())}{bcolors['ENDC']} User interrupt! Shutting down")
    stop_proxy()

# Function to get current IP
def ip():
    while True:
        try:
            response = requests.get(IP_API)
            response.raise_for_status()  # Raise an exception for 4xx or 5xx status codes
            json_res = response.json()
            ip_txt = json_res["ip"]
            break
        except requests.RequestException as e:
            print(f"Error: {e}. Retrying...")
            continue
    return ip_txt

# Function to check if script is running with root privileges
def check_root():
    """Check if the script is running with root privileges"""
    if os.geteuid() != 0:
        print("Error: Root privileges are required. Please run with 'sudo'.")
        sys.exit(1)  # Exit with a non-zero status code to indicate an error

# Function to start proxy
def start_proxy():
    print("Setting up proxy...")
    # Set up environment variables
    os.environ["HTTP_PROXY"] = PROXY_URL
    os.environ["HTTPS_PROXY"] = PROXY_URL
    # Set up iptables rules (optional)
    iptables_rules = """
    iptables -F
    iptables -t nat -F
    iptables -t nat -A OUTPUT -p tcp --syn -j REDIRECT --to-ports 8080
    """
    os.system(iptables_rules)
    print("Proxy setup complete!")
    print("CURRENT IP: " + ip())

# Function to stop proxy
def stop_proxy():
    print(bcolors["RED"] + "STOPPING proxy" + bcolors["ENDC"])
    print(" Flushing iptables, resetting to default")
    # Remove the proxy environment variables
    del os.environ["HTTP_PROXY"]
    del os.environ["HTTPS_PROXY"]
    # Flush iptables rules
    iptables_flush = """
    iptables -P INPUT ACCEPT
    iptables -P FORWARD ACCEPT
    iptables -P OUTPUT ACCEPT
    iptables -t nat -F
    iptables -t mangle -F
    iptables -F
    iptables -X
    """
    os.system(iptables_flush)
    print(bcolors["GREEN"] + "[done]" + bcolors["ENDC"])
    print(" Restarting Network manager")
    os.system("service network-manager restart")
    print(bcolors["GREEN"] + "[done]" + bcolors["ENDC"])
    print(" Fetching current IP...")
    time.sleep(3)
    print(" CURRENT IP: " + bcolors["GREEN"] + ip() + bcolors["ENDC"])

# Function to check for update

def check_update():
    print(t() + ' Checking for update...')
    try:
        response = requests.get(LATEST_RELEASE_API)
        response.raise_for_status()  # Raise an exception for 4xx or 5xx status codes
        json_data = json.loads(response.content)
        new_version = json_data["tag_name"][1:]
        print(new_version)
        if packaging.version.parse(new_version) > packaging.version.parse(VERSION):
            print(t() + bcolors["GREEN"] + ' New update available!' + bcolors["ENDC"])
            print(t() + ' Your current ProxyGhost version : ' + bcolors["GREEN"] + VERSION + bcolors["ENDC"])
            print(t() + ' Latest ProxyGhost version available : ' + bcolors["GREEN"] + new_version + bcolors["ENDC"])
            choice = input(bcolors["BOLD"] + "Would you like to download latest version and build from Git repo? [Y/n]" + bcolors["ENDC"]).lower()
            if choice in {'yes', 'y', 'ye', ''}:
                try:
                    os.system('cd /tmp && git clone https://github.com/RoggersOgao/proxyGhost.git')
                    os.system('cd /tmp/proxyghost && sudo ./proxybuild.sh')
                except Exception as e:
                    print(f"Error: {e}")
            elif choice in {'no', 'n'}:
                print(t() + " Update aborted by user")
            else:
                print("Please respond with 'yes' or 'no'")
        else:
            print(t() + " ProxyGhost is up to date!")
    except requests.RequestException as e:
        print(f"Error: {e}. Unable to check for update.")

# Main function
def main():
    check_root()
    if len(sys.argv) <= 1:
        check_update()
        usage()
    try:
        (opts, args) = getopt.getopt(sys.argv[1:], 'srxhu', [
            'start', 'stop', 'switch', 'help', 'update'])
    except (getopt.GetoptError):
        usage()
        sys.exit(2)
    for (o, a) in opts:
        if o in ('-h', '--help'):
            usage()
        elif o in ('-s', '--start'):
            start_proxy()
        elif o in ('-x', '--stop'):
            stop_proxy()
        elif o in ('-u', '--update'):
            check_update()
        else:
            usage()

if __name__ == '__main__':
    signal.signal(signal.SIGINT, sigint_handler)
    main()
