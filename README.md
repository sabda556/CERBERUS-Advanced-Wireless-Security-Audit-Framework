Legal
Use only on networks you own or have written authorization to test. Unauthorized access is illegal. The author assumes no liability for misuse.

Features
6 attack vectors: Handshake capture, PMKID clientless, WPS Pixie Dust, WPA3-Transition downgrade, Evil Twin captive portal, WEP fragmentation
Intelligent chaining: Automatically selects and runs vectors based on target encryption type. Exits on first success.
Dual cracking: aircrack-ng (CPU) + hashcat (GPU, mode 22000)
Real-time animations: Dot-sequence progress indicators for all waiting operations
Stealth mode: MAC randomization via macchanger
No pip dependencies: Python standard library only
Requirements
Hardware
Wireless adapter with monitor mode and packet injection (e.g. Alfa AWUS036ACH, TP-Link TL-WN722N v1)

Software
bash



sudo apt install aircrack-ng hostapd dnsmasq reaver bully hashcat \
                 hcxdumptool hcxpcapngtool tshark iw macchanger iptables
Python 3.7+ (standard library only)

Installation
bash



git clone https://github.com/sabda556/CERBERUS-Advanced-Wireless-Security-Audit-Framework.git
cd CERBERUS-Advanced-Wireless-Security-Audit-Framework
chmod +x CERBERUS.py
Usage
bash



sudo python3 CERBERUS.py [options]
Root privileges required for raw socket access and monitor mode.

Options


Flag	Default	Description
-i, --interface	auto-detect	Wireless interface (e.g. -i wlan1)
-w, --wordlist	/usr/share/wordlists/rockyou.txt	Dictionary file path
--scan-time	20	Network discovery duration (seconds)
--handshake-timeout	120	Handshake capture window (seconds)
--wps-timeout	300	WPS attack window (seconds)
--evil-twin	off	Enable Evil Twin captive portal
--stealth	off	Randomize MAC before scanning
Examples
bash



# Default run
sudo python3 CERBERUS.py

# Specify interface and wordlist
sudo python3 CERBERUS.py -i wlan1 -w /opt/wordlists/rockyou.txt

# Extended scan with Evil Twin
sudo python3 CERBERUS.py --scan-time 30 --evil-twin

# Stealth mode
sudo python3 CERBERUS.py --stealth
Attack Vectors
WPA2 4-Way Handshake
Uses airodump-ng to capture the EAPOL 4-way handshake. Injects deauth packets (3 attempts) to force client re-association. Cracks offline with aircrack-ng or hashcat -m 22000.

PMKID Clientless
Captures RSN PMKID from AP beacon using hcxdumptool. No clients or deauth required. Cracked via hashcat -m 22000.

WPS Pixie Dust
Uses reaver -K 1 to exploit weak WPS RNG. Falls back to bully online PIN brute force. Derives WPA2 password from recovered PIN via wpa_passphrase.

WPA3-Transition Downgrade
Detects WPA3-Transition mode (SAE + PSK). Broadcasts a WPA2-only rogue AP via hostapd, forcing client downgrade. Captures WPA2 handshake.

Evil Twin
Creates rogue AP with cloned SSID + _Free suffix. Serves credential-harvesting captive portal via hostapd + dnsmasq + Python HTTP server. All traffic redirected to portal.

WEP
Fragmentation attack (aireplay-ng -5) → ARP replay → IV collection → aircrack-ng -K KoreK attack.

Attack Flow



Scan → Interface selection → Monitor mode → Discovery
  │
  ├── WPA3 → [Down-grade] → [WPS] → [Evil Twin]
  ├── WPA2 → [WPS] → [PMKID] → [Handshake] → [Evil Twin]
  ├── WEP  → [Fragmentation] → [ARP Replay] → [aircrack -K]
  └── Open → No password needed
Each vector exits on success. Next vector runs only if previous one fails.

Session Example



[06:42:39] * checking for wireless device . , .. , ...
[06:42:41] + found #3 devices : wlan0, wlan1, wlp2s0
[06:42:44] * enabling monitor mode on wlan0 . , ..
[06:42:46] + monitor interface ready : wlan0mon

:: STEP 1 — NETWORK DISCOVERY ::

[06:42:46] * scanning all channels (20s) . , ..
[06:43:06] + found #12 targets!

  #   PRIVACY                  BSSID            CH   PWR  ESSID
  ────────────────────────────────────────────────────────────────────
  1    WPA2 CCMP PSK       AA:BB:CC:DD:EE:01   CH 6   -45  wifi_rumah
  2    WPA3 SAE PSK        BB:CC:DD:EE:FF:02   CH 1   -62  secure_net
  3    WPA2 CCMP PSK       CC:DD:EE:FF:AA:03   CH11   -55  wifi_kantor

CERBERUS> please select the target : 1
[06:43:08] $ locked target : wifi_rumah (AA:BB:CC:DD:EE:01)

:: STEP 2 — ATTACK SURFACE : wifi_rumah (WPA2 CCMP PSK) ::

:: STEP 3 — WPA/WPA2 ATTACK VECTORS ::

[06:43:08] > deploying multi-vector attack against wifi_rumah
[06:43:08] > launching PMKID clientless attack ...
[06:43:23] * hcxdumptool gathering PMKID frames ...
[06:43:38] ! no PMKID obtained from target
[06:43:38] > initializing WPA2 4-way handshake capture ...
[06:43:46] > forcing client re-association (deauth injection) ...
[06:43:54] $ WPA2 4-way handshake captured!
[06:43:54] * cracking with aircrack-ng + rockyou.txt ...
[06:53:54] $ KEY FOUND! [ Cont0hPassword123 ]

:: STEP 4 — RESULT ::

  ██████╗ ██████╗ ███╗   ██╗ ██████╗ ██████╗ █████╗ ████████╗███████╗
  ██╔════╝██╔═══██╗████╗  ██║██╔════╝ ██╔══██╗██╔══██╗╚══██╔══╝██╔════╝
  ██║     ██║   ██║██╔██╗ ██║██║  ██╗ ██████╔╝███████║   ██║   █████╗
  ██║     ██║   ██║██║╚██╗██║██║  ╚██╗██╔══██╗██╔══██║   ██║   ██╔══╝
  ╚██████╗╚██████╔╝██║ ╚████║╚██████╔╝██║  ██║██║  ██║   ██║   ███████╗
   ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   ╚══════╝

[06:53:54] $ SUCCESS! PASSWORD FOUND from wifi_rumah [Cont0hPassword123]
[06:53:54] * restoring adapter state ...
[06:53:56] $ closing! (authorized wireless audit completed)
Output Structure



cerberus_capture/
├── scan-01.csv                          # Raw scan output
├── AA_BB_CC_DD_EE_01/                   # Per-target (BSSID)
│   ├── wpa2_capture-01.cap              # Handshake capture
│   ├── pmkid.hc22000                    # PMKID hash
│   ├── wps_pixie.txt                    # Reaver output
│   ├── captured_credentials.txt         # Evil Twin creds
│   ├── hashcat.out                      # Cracked passwords
│   └── portal/                          # Captive portal HTML
Troubleshooting


Problem	Solution
No interface found	sudo airmon-ng, lsusb, install adapter driver
Monitor mode failed	sudo systemctl stop NetworkManager, retry
Permission denied	Run with sudo
Missing tools	sudo apt install aircrack-ng hostapd dnsmasq reaver bully hashcat hcxdumptool hcxpcapngtool iw macchanger
Processes left behind	sudo pkill -f airodump-ng; sudo pkill -f hostapd; sudo pkill -f dnsmasq
Architecture



CERBERUS
├── WirelessInterface    — Hardware detection, monitor mode, MAC stealth
├── Scanner              — Network discovery, CSV parsing
├── AttackEngine         — All 6 attack vectors + GPU cracking
├── Cerberus (main)      — Orchestration, flow control, result display
└── UI                   — Animated progress, status messages, headers
License
MIT License. See LICENSE file.

Save this as README.md and push:

bash



nano README.md
# paste content, save

git add README.md
git commit -m "Simplify README — clean, focused documentation"
git push
