# 🛠️ **WifitoolP v0.1 (Python Version)**

A simple Python-based tool to demonstrate the process of Wi-Fi network auditing. Features include:
- Checking for required tools
- Putting the Wi-Fi adapter into monitor mode
- Scanning available networks
- Capturing WPA handshake
- Cracking password using a wordlist (brute-force)

> ⚠️ **Warning**: This program is for **educational purposes only**. The author is not responsible for any illegal or unethical use.

---

## 🔧 Requirements

- **OS**: Linux (tested on Kali Linux, Ubuntu)
- **Permissions**: root (run with `sudo`)
- **Dependencies**:
  - `aircrack-ng`
  - `xterm` (checked in code, though not used)
  - `iw`
  - Python 3.6+

---

## 🚀 How to Run

```bash
sudo python3 script.py
```

> Make sure your Wi-Fi adapter supports monitor mode.

---

## 📋 Main Menu Functions

| Command | Description |
|-------|-----------|
| `0` or `?` | Show help |
| `1` | Check and install required components |
| `2` | Enable monitor mode on Wi-Fi interface |
| `3` | Scan nearby Wi-Fi networks |
| `4` | Capture handshake (deauthentication + listening) |
| `5` | Crack password using wordlist |

---

## 📂 Execution Flow

1. **Initialization**
   - Cleans up after previous runs
   - Detects the Wi-Fi interface (e.g., `wlan0`)

2. **Check Components (`1`)**
   - Checks for `aircrack-ng`, `xterm`, `iw`
   - Installs missing tools via `apt` if needed

3. **Enable Monitor Mode (`2`)**
   - Kills interfering processes: `airmon-ng check kill`
   - Starts monitor mode: `airmon-ng start wlanX`
   - Creates monitor interface `wlanXmon`

4. **Scan Networks (`3`)**
   - Runs `airodump-ng` for ~9 seconds
   - Saves output to `nets.csv-01.csv`
   - Parses and displays discovered networks
   - Prompts user to select a network by name
   - Saves BSSID and channel to `tmp/`

5. **Capture Handshake (`4`)**
   - Starts `airodump-ng` on selected network
   - Sends periodic deauthentication packets to force handshake
   - On `Ctrl+C`, assumes handshake was captured
   - Saves capture to `tmp/network_name.cap`

6. **Password Cracking (`5`)**
   - Looks for `list.txt` (wordlist)
   - Finds `.cap` file in `tmp/`
   - Runs: `aircrack-ng -w list.txt file.cap`
   - Copies `.cap` file to the root directory

---

## 📁 Temporary Files & Directories

- `tmp/` — stores temporary `.cap`, `.txt` files
- `nets.csv-01.csv` — scan results
- `.cap` — handshake capture files

---

## 🧹 Automatic Cleanup

On startup and exit:
- Stops monitor mode
- Removes `tmp/` directory
- Deletes old `.csv` files

---

## ⚙️ Global Variables

```python
current_progress = 0           # Current progress (0–100%)
ctrlc_pressed = False          # Flag for Ctrl+C handling
wireless_card = ""             # Main interface (e.g., wlan0)
wireless_card_monitormode = "" # Monitor interface (e.g., wlan0mon)
target_name = ""               # Selected network name
target_bssid = ""              # BSSID of selected network
target_channel_number = ""     # Channel number
```

---

## 🛑 Error Handling

- Checks for root privileges
- Validates required tools
- Verifies file existence
- Handles `KeyboardInterrupt` (`Ctrl+C`)

---

## 📝 Recommendations

1. **Create a wordlist (`list.txt`)**:
   ```bash
   echo "password123" > list.txt
   echo "qwerty" >> list.txt
   ```

2. **Always run with root**:
   ```bash
   sudo python3 script.py
   ```

3. **Fix interface issues**:
   - Reboot the system
   - Or manually stop NetworkManager:
     ```bash
     sudo systemctl stop NetworkManager
     ```

---

## 📎 Author & License

- **Author**: GigaCode (Sber)
- **Version**: 0.1 (Python)
- **License**: Educational Use Only

---

Let me know if you'd like:
- Logging functionality
- Manual interface selection
- Auto-generated wordlists
- GUI wrapper
- Progress persistence

Type `?` in the program to return to help.

--- 

✅ Ready for use in learning and ethical security testing.
