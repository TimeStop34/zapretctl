"""Вспомогательные функции."""

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .constants import ETC_OS_RELEASE, PROC_MOUNTS

JSON_OUTPUT = False

def set_json_output(enabled: bool):
    global JSON_OUTPUT
    JSON_OUTPUT = enabled

def print_output(data, error=False, exit_code=0):
    if JSON_OUTPUT:
        if isinstance(data, str):
            data = {"message": data}
        elif not isinstance(data, (dict, list)):
            data = {"data": data}
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        if isinstance(data, (dict, list)):
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            print(data)
    if error:
        sys.exit(1 if exit_code == 0 else exit_code)
    elif exit_code != 0:
        sys.exit(exit_code)

def run_cmd(cmd: List[str], check: bool = True, capture: bool = True, timeout: int = 30) -> Tuple[int, str, str]:
    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE if capture else None,
            stderr=subprocess.PIPE if capture else None,
            text=True,
            check=check,
            timeout=timeout
        )
        return proc.returncode, proc.stdout.strip() if capture else "", proc.stderr.strip() if capture else ""
    except subprocess.CalledProcessError as e:
        if check:
            raise
        return e.returncode, e.stdout.strip() if capture else "", e.stderr.strip() if capture else ""
    except subprocess.TimeoutExpired as e:
        return 124, "", f"Timeout after {timeout}s"

def is_root() -> bool:
    return os.geteuid() == 0

def require_root():
    if not is_root():
        print_output("Требуются права суперпользователя.", error=True)

def get_os_info() -> Dict[str, str]:
    info = {"ID": "", "ID_LIKE": ""}
    if ETC_OS_RELEASE.exists():
        with open(ETC_OS_RELEASE) as f:
            for line in f:
                if line.startswith("ID="):
                    info["ID"] = line.split("=", 1)[1].strip().strip('"')
                elif line.startswith("ID_LIKE="):
                    info["ID_LIKE"] = line.split("=", 1)[1].strip().strip('"')
    return info

def is_openwrt() -> bool:
    return get_os_info()["ID"] == "openwrt"

def check_filesystem_rw() -> bool:
    if PROC_MOUNTS.exists():
        with open(PROC_MOUNTS) as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 4 and parts[1] == "/":
                    return parts[3] != "ro"
    return True

def detect_init_system() -> str:
    if Path("/run/systemd/system").exists():
        return "systemd"
    if is_openwrt():
        return "procd"
    if shutil.which("openrc"):
        return "openrc"
    if shutil.which("runit"):
        os_id = get_os_info()["ID"]
        if os_id == "artix":
            return "runit-artix"
        return "runit"
    if Path("/sbin/init").exists():
        _, out, _ = run_cmd(["/sbin/init", "--version"], check=False)
        if "sysv init" in out.lower():
            return "sysvinit"
    return "unknown"

def get_firewall_type() -> str:
    if shutil.which("iptables"):
        _, out, _ = run_cmd(["iptables", "--version"], check=False)
        if "legacy" in out.lower():
            return "iptables"
        elif "nf_tables" in out.lower():
            return "nftables"
    return "nftables"

def is_zapret_installed() -> bool:
    return (Path("/opt/zapret/binaries")).exists()

def get_current_version() -> Optional[str]:
    ver_file = Path("/opt/zapret-ver")
    if ver_file.exists():
        return ver_file.read_text().strip()
    return None

def sha256sum(path: Path) -> str:
    import hashlib
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            h.update(chunk)
    return h.hexdigest()

def parse_address_list(input_str: str) -> List[str]:
    # заменяем разделители , | на пробелы и разбиваем
    normalized = re.sub(r'[,|]', ' ', input_str)
    return [addr.strip() for addr in normalized.split() if addr.strip()]

def is_ip_address(addr: str) -> bool:
    """Проверяет, является ли строка IP-адресом (IPv4 или IPv6)."""
    import ipaddress
    try:
        ipaddress.ip_address(addr)
        return True
    except ValueError:
        return False

