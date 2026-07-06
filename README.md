CERBERUS — Advanced Wireless Security Audit Framework
CERBERUS is a multi-vector automated wireless security auditor designed for professional Wi-Fi network security assessments. The framework integrates popular open-source tools into a unified command-line interface with automatic attack chaining and intelligence-driven vector selection based on the target's encryption type.

Warning: This tool is only for use on networks you own or have written authorization to test. Misuse beyond legal authority is a criminal offense in virtually all jurisdictions.

Core Features


Feature	Description
Multi-Protocol	Supports WEP, WPA, WPA2-PSK, WPA3-SAE, WPA3-Transition
Automatic Attack Chaining	Intelligently selects and executes attack vectors based on scan results. If one vector fails, the system chains to the next without user intervention
6+ Attack Vectors	Handshake capture, PMKID clientless, WPS Pixie Dust, WPA3 downgrade, Evil Twin captive portal, WEP IV fragmentation
Dual Offline Cracking	aircrack-ng (CPU) + hashcat (GPU) for maximum flexibility
Real-time Status Animation	Dot-sequence animated progress indicators (., .., ...) for all waiting operations
Stealth Mode	Automatic MAC address randomization via macchanger
Robust Error Handling	Bounded retry loops for user input, tracked background process cleanup, graceful degradation on failure
Session Logging	Per-target output directories with capture files, credentials, and logs
Attack Vector Flow
The framework automatically selects and chains vectors based on scan results. The decision tree:




[Scan Complete]
     │
     ├── WPA3 → [Transition Mode?]
     │              ├── Yes → [WPA3 Downgrade] → [WPS Pixie Dust] → [Evil Twin]
     │              └── No  → [WPS Pixie Dust] → [Evil Twin]
     │
     ├── WPA2/WPA → [WPS Advertised?]
     │                 ├── Yes → [WPS Pixie Dust] → [PMKID Clientless] → [4-Way Handshake] → [Evil Twin]
     │                 └── No  → [PMKID Clientless] → [4-Way Handshake] → [Evil Twin]
     │
     ├── WEP → [IV Capture + Fragmentation + ARP Replay → aircrack-ng -K]
     │
     └── Open → No password needed (informational only)
Each vector exits early on success. If all passive vectors fail, the Evil Twin (active social engineering) vector can be enabled with --evil-twin.

Attack Vectors in Detail
1. WPA2 4-Way Handshake Capture
Tools: airodump-ng, aireplay-ng, aircrack-ng / hashcat
Method: Hops to target channel, listens for the EAPOL 4-way handshake. If no handshake appears naturally, injects deauthentication packets (3 attempts with random intervals) to force client re-association.
Cracking: Offline dictionary attack via aircrack-ng (CPU) or hashcat (GPU, mode 22000).
2. PMKID Clientless Attack
Tools: hcxdumptool, hcxpcapngtool, hashcat
Method: Captures the RSN PMKID from beacon/probe response frames. Does not require any connected clients or deauth injection.
Cracking: hashcat mode 22000 (PMKID+EAPOL). GPU accelerated.
3. WPS Pixie Dust + Online PIN Brute Force
Tools: reaver, bully
Method:
Pixie Dust (reaver -K 1): Exploits weak RNG in WPS registrar implementations to recover the WPS PIN in minutes.
Fallback (bully): If Pixie Dust fails, online PIN brute-force with adaptive timing.
PIN → Password: The WPS PIN is fed through wpa_passphrase to derive the WPA2 PSK.
4. WPA3-Transition Mode Downgrade
Tools: hostapd, airodump-ng, aircrack-ng
Method: Detects WPA3-Transition mode (Mixed WPA3/WPA2). Broadcasts a rogue WPA2-only access point with the same SSID, forcing client devices to fall back to WPA2. Captures the WPA2 4-way handshake when clients connect.
Requirement: The target must be in Transition mode (SAE + PSK), not WPA3-only (SAE only).
5. Evil Twin + Captive Portal (Social Engineering)
Tools: hostapd, dnsmasq, iptables, Python http.server
Method: Creates a rogue access point with a cloned SSID (appended with _Free to attract opportunistic connections). Serves a credential-harvesting captive portal page via HTTPS redirect. DNS spoofs all requests to the local portal IP.
Credential Capture: Captures POST form data (username + password) to captured_credentials.txt.
6. WEP Attack
Tools: aireplay-ng, aircrack-ng
Method: Fragmentation attack (-5) to generate PRGA XOR keystream → ARP injection to flood the network with IVs → aircrack-ng KoreK attack (-K) on captured IVs.
Note: WEP is deprecated. This vector exists for legacy network testing.
Requirements
Hardware
A wireless adapter supporting monitor mode and packet injection (e.g., Alfa AWUS036ACH/ACS, TP-Link TL-WN722N v1, or any chipset with mac80211 + cfg80211 support)
Software (Kali Linux / Parrot OS / Debian-based)
bash



sudo apt install aircrack-ng hostapd dnsmasq reaver bully hashcat hcxdumptool hcxpcapngtool tshark iw macchanger iptables
Python
Python 3.7+ (standard library only — no external pip packages required)
Installation
bash



git clone https://github.com/your-username/cerberus.git
cd cerberus
chmod +x cerberus.py
Or download the single file directly:

bash



wget https://raw.githubusercontent.com/your-username/cerberus/main/cerberus.py
chmod +x cerberus.py
Usage
bash



sudo python3 cerberus.py [options]
All operations require root privileges for raw socket access, monitor mode, and packet injection.

Options


Option	Default	Description
-i, --interface	auto-detect	Specify wireless interface (e.g., wlan0, wlan1). Overrides auto-detection
-w, --wordlist	/usr/share/wordlists/rockyou.txt	Path to dictionary file for offline cracking
--scan-time	20	Duration of network discovery scan in seconds
--handshake-timeout	120	Window to capture 4-way handshake in seconds
--wps-timeout	300	Maximum time for WPS attack attempts in seconds
--evil-twin	False	Enable Evil Twin captive portal attack as last resort
--stealth	False	Randomize MAC address before scanning
Examples
bash



# Basic run with auto-detection
sudo python3 cerberus.py

# Specify interface and wordlist
sudo python3 cerberus.py -i wlan1 -w /opt/wordlists/rockyou.txt

# Extended scan and handshake timeout
sudo python3 cerberus.py --scan-time 30 --handshake-timeout 180

# Stealth mode with Evil Twin enabled
sudo python3 cerberus.py --stealth --evil-twin

# Long WPS attack window
sudo python3 cerberus.py --wps-timeout 600
Program Flow



┌──────────────────────────────────────┐
│            CERBERUS                   │
│    Advanced Wireless Audit Framework   │
└──────────────────────────────────────┘
                    │
   [06:42:39] * checking for wireless device . , .. , ...
   [06:42:41] + found #3 wireless devices : wlan0, wlan1, wlp2s0
                    │
                    ▼
   ┌─── Interface Pick (auto or -i) ───┐
   │ Select monitor interface           │
   └────────────────────────────────────┘
                    │
                    ▼
   [06:42:44] * enabling monitor mode on wlan0 . , .. 
   [06:42:46] + monitor interface ready : wlan0mon
                    │
                    ▼
═══════════════════════════════════════════════
  :: STEP 1 — NETWORK DISCOVERY ::
═══════════════════════════════════════════════
   [06:42:46] * scanning all channels (20s) . , .. , ...
   [06:43:06] + found #12 targets!
                    │
                    ▼
   #   PRIVACY                BSSID            CH   PWR  ESSID / WPS
   ───────────────────────────────────────────────────────────────────
   1     WPA2 CCMP PSK    AA:BB:CC:DD:EE:01   CH 6   PWR -45   wifi_rumah
   2     WPA2 CCMP PSK    BB:CC:DD:EE:FF:02   CH 1   PWR -62   wifi_kantor  [WPS]
   3     WPA3 SAE PSK     CC:DD:EE:FF:AA:03   CH11   PWR -55   secure_net
   ...
                    │
                    ▼
   CERBERUS> please select the target : 1
   [06:43:08] $ locked target : wifi_rumah (AA:BB:CC:DD:EE:01) — WPA2 CCMP PSK
                    │
                    ▼
═══════════════════════════════════════════════
  :: STEP 2 — ATTACK SURFACE ::
═══════════════════════════════════════════════

═══════════════════════════════════════════════
  :: STEP 3 — WPA/WPA2 ATTACK VECTORS ::
═══════════════════════════════════════════════
   [06:43:08] > deploying multi-vector attack against wifi_rumah
   
   [06:43:08] > launching PMKID clientless attack ...
   [06:43:23] * hcxdumptool gathering PMKID frames ...  
   [06:43:38] ! no PMKID obtained from target
   
   [06:43:38] > initializing WPA2 4-way handshake capture ...
   [06:43:43] > forcing client re-association (deauth injection) ...
   [06:43:48] $ WPA2 4-way handshake captured!
   [06:43:50] * cracking with aircrack-ng + rockyou.txt ...
   [06:53:50] $ KEY FOUND! [ Cont0hPassword123 ]
                    │
                    ▼
═══════════════════════════════════════════════
  :: STEP 4 — RESULT ::
═══════════════════════════════════════════════

 
   ██████╗ ██████╗ ███╗   ██╗ ██████╗ ██████╗  █████╗ ████████╗███████╗
  ██╔════╝██╔═══██╗████╗  ██║██╔════╝ ██╔══██╗██╔══██╗╚══██╔══╝██╔════╝
  ██║     ██║   ██║██╔██╗ ██║██║  ███╗██████╔╝███████║   ██║   █████╗
  ██║     ██║   ██║██║╚██╗██║██║   ██║██╔══██╗██╔══██║   ██║   ██╔══╝
  ╚██████╗╚██████╔╝██║ ╚████║╚██████╔╝██║  ██║██║  ██║   ██║   ███████╗
   ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   ╚══════╝
   [06:53:50] $ SUCCESS! PASSWORD FOUND from wifi_caffe [Examp1ePassword123]
   [06:53:50] * restoring adapter state . , ..
   [06:53:52] $ closing! (authorized wireless audit completed)
Output Directory Structure



cerberus_capture/
├── scan-01.csv                       # Raw airodump-ng scan results
├── AA_BB_CC_DD_EE_01/                # Per-target directory (BSSID-based)
│   ├── wpa2_capture-01.cap           # Captured handshake (if applicable)
│   ├── pmkid.hc22000                 # PMKID hash (hashcat format)
│   ├── wps_pixie.txt                 # Reaver output
│   ├── bully.txt                     # Bully output
│   ├── hostapd_downgrade.conf        # WPA3 downgrade AP config
│   ├── evil_twin_hostapd.conf        # Evil Twin AP config
│   ├── portal/                       # Captive portal HTML
│   ├── captured_credentials.txt      # Evil Twin captured creds
│   ├── hashcat.out                   # Hashcat cracking output
│   └── proc_*.log                    # Background process logs
Troubleshooting
"No wireless interface found"
bash



# Check if your adapter is detected
iwconfig
ip link
lsusb | grep -i wireless

# Install driver (example for Realtek RTL8812AU)
sudo apt install realtek-rtl88xxau-dkms
sudo modprobe 8812au
"Monitor mode failed"
Ensure no NetworkManager interference: sudo systemctl stop NetworkManager
Try manually: sudo airmon-ng start wlan0
"No wordlist available"
bash



# Download rockyou
wget https://github.com/brannondorsey/naive-hashcat/releases/download/data/rockyou.txt
# Or use Kali's package
sudo apt install wordlist
Permission denied
Always run with sudo python3 cerberus.py
Verify: sudo -v
Process cleanup issues
On Ctrl+C, CERBERUS sends SIGTERM → SIGKILL to all spawned child processes
Manual cleanup: sudo pkill -f airodump-ng; sudo pkill -f hostapd; sudo pkill -f dnsmasq
Technical Architecture



┌─────────────────────────────────────────────────────────────┐
│                       cerberus.py                            │
├─────────────────────────────────────────────────────────────┤
│  WirelesInterface    │  Scanner     │  AttackEngine          │
│  ├─ detect()         │  ├─ scan()   │  ├─ wpa2_handshake()  │
│  ├─ enable_monitor() │  └─ _parse() │  ├─ pmkid_attack()    │
│  ├─ disable_monitor()│              │  ├─ wps_attack()      │
│  └─ randomize_mac()  │              │  ├─ wpa3_downgrade()  │
│                       │              │  ├─ evil_twin()       │
│                       │              │  └─ _hashcat_attack() │
├─────────────────────────────────────────────────────────────┤
│  Cerberus (Orchestrator)                                     │
│  ├─ run()                                                    │
│  ├─ _attack_wpa2() / _attack_wpa3() / _attack_wep()         │
│  └─ _conclude()                                              │
├─────────────────────────────────────────────────────────────┤
│  Utilities: animated_wait(), status(), header()               │
└─────────────────────────────────────────────────────────────┘
All attack vectors operate inside AttackEngine which tracks every spawned subprocess via _background_procs[]. The orchestrator Cerberus class controls the flow and handles cleanup via signal.SIGINT handler and try/finally blocks.

Known Limitations


Limitation	Reason
WPA3-SAE only (no Transition)	WPA3 handshake cracking is infeasible without specific client-side vulnerabilities (e.g., Dragonblood). Only Transition-mode downgrade is supported
WPS PIN derivation is PIN → PSK	Only applies to certain router models. Many PIN recovery databases exist but are not bundled
Wordlist-only cracking	No rule-based or hybrid mask generation yet. Use external hashcat rules for advanced attacks
Single monitor interface	Chains vectors sequentially. No distributed/parallel attack over multiple radios
Python HTTP server (single-thread)	Evil Twin portal performance degrades under high concurrent connections
License
MIT License — see LICENSE file for details.

Disclaimer
This software is provided for educational purposes and authorized security testing only. The authors assume no liability for misuse or damage caused by this tool. Users are responsible for complying with all applicable laws and obtaining proper authorization before testing any network.





Save this as `README.md` in your repository root.

---

## Repository setup command

```bash
# Create README
nano README.md
# Paste the full content above, save

# Initialize git and push
git init
git add README.md cerberus.py
git commit -m "Initial release: CERBERUS v1.0 — Advanced Wireless Security Audit Framework"
git branch -M main
git remote add origin https://github.com/your-username/cerberus.git
git push -u origin main
