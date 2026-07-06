Legal

Use only on networks you own or have written authorization to test. Unauthorized access is illegal. The author assumes no liability for misuse.

Download

bash



git clone https://github.com/sabda556/CERBERUS-Advanced-Wireless-Security-Audit-Framework.git

cd CERBERUS-Advanced-Wireless-Security-Audit-Framework

chmod +x CERBERUS.py

Or download the single file directly:

bash



wget https://raw.githubusercontent.com/sabda556/CERBERUS-Advanced-Wireless-Security-Audit-Framework/main/CERBERUS.py

chmod +x CERBERUS.py

Requirements

Hardware: Wireless adapter with monitor mode and packet injection.

Software:

bash



sudo apt install aircrack-ng hostapd dnsmasq reaver bully hashcat \
                 hcxdumptool hcxpcapngtool tshark iw macchanger iptables
Python 3.7+ (standard library only — no external pip packages required)

Usage

bash

sudo python3 CERBERUS.py

Root privileges required for raw socket access and monitor mode.

Options


Flag	Default	Description

-i, --interface	auto-detect	Specify wireless interface

-w, --wordlist	/usr/share/wordlists/rockyou.txt	Path to dictionary file

--scan-time	20	Network discovery duration in seconds

--handshake-timeout	120	Handshake capture window in seconds

--wps-timeout	300	WPS attack window in seconds

--evil-twin	off	Enable Evil Twin captive portal attack

--stealth	off	Randomize MAC address before scanning

Features

Supported Protocols

WEP, WPA, WPA2-PSK, WPA3-SAE, WPA3-Transition

Attack Vectors

WPA2 4-Way Handshake Capture — Captures EAPOL handshake via airodump-ng with deauth injection to force client re-association. Cracks offline with 

aircrack-ng or hashcat mode 22000.

PMKID Clientless Attack — Captures RSN PMKID from AP beacon using hcxdumptool. No clients or deauth required. Cracked via hashcat.

WPS Pixie Dust — Exploits weak WPS RNG using reaver. Falls back to online PIN brute force with bully. Derives WPA2 password from recovered PIN.

WPA3-Transition Downgrade — Detects mixed WPA3/WPA2 mode. Broadcasts WPA2-only rogue AP via hostapd to force client fallback, then captures WPA2 

handshake.

Evil Twin Captive Portal — Creates rogue AP with cloned SSID. Serves credential-harvesting portal via hostapd, dnsmasq, and Python HTTP server with 

DNS spoofing and HTTP redirect.

WEP Fragmentation — Fragmentation attack generates PRGA keystream, ARP replay floods IVs, aircrack-ng KoreK attack cracks the key.

Intelligence

Automatic attack chaining — Selects and runs vectors based on detected encryption type. Exits immediately on success. Falls through to next vector 

only if previous one fails.

WPA3 detection — Distinguishes between Transition mode (downgradable) and SAE-only (immune).

Cracking

Dual engine — aircrack-ng for CPU, hashcat mode 22000 for GPU acceleration.

Multi-wordlist fallback — Automatically searches alternate wordlist paths if default is missing.

Interface

5-method wireless detection — iw dev, iwconfig, sysfs, ip link regex, phy80211 fallback chain
.
Real-time dot animation — All waiting operations show cycling . .. ... progress.

Stealth mode — MAC address randomization via macchanger before scanning.

Stability

Tracked background processes — Every spawned subprocess is tracked and cleaned up via SIGTERM then SIGKILL.

Bounded input loops — Target selection and interface selection have capped retry limits with explicit quit option.

Graceful degradation — If monitor mode fails or no interfaces exist, tool exits with actionable error message.

Output

Per-target directories — All captures, logs, and cracked passwords organized by BSSID.

Session logging — Background process logs, hashcat output, captured credentials.

Program Flow

Interface detection and selection

Monitor mode activation

Network discovery scan

Target selection from discovered networks

Automatic attack vector selection based on encryption type

Multi-vector attack chain with early exit on success

Result display and adapter state restoration

Architecture

WirelessInterface — Hardware detection, monitor mode control, MAC stealth

Scanner — Network discovery via airodump-ng with fault-tolerant CSV parsing

AttackEngine — All six attack vectors with background process tracking

Cerberus (Orchestrator) — Flow control, vector routing, cleanup handling

UI Engine — Animated progress indicators, timestamped status messages, section headers

License

MIT License.
