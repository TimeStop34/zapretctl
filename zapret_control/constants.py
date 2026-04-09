"""Константы и пути."""

from pathlib import Path

ZAPRET_DIR = Path("/opt/zapret")
ZAPRET_INSTALLER_DIR = Path("/opt/zapret.installer")
ZAPRETCTL_DIR = Path("/opt/zapretctl")

ZAPRET_CONFIG_FILE = ZAPRET_DIR / "config"
ZAPRET_HOSTS_USER_FILE = ZAPRET_DIR / "ipset" / "zapret-hosts-user.txt"
ZAPRET_HOSTS_EXCLUDE_FILE = ZAPRET_DIR / "ipset" / "zapret-hosts-user-exclude.txt"
ZAPRET_GAME_IPSET_FILE = ZAPRET_DIR / "ipset" / "ipset-game.txt"
ZAPRET_VERSION_FILE = Path("/opt/zapret-ver")

ZAPRET_CFGS_DIR = ZAPRET_DIR / "zapret.cfgs"
ZAPRET_CFGS_CONFIG_DIR = ZAPRET_CFGS_DIR / "configurations"
ZAPRET_CFGS_LISTS_DIR = ZAPRET_CFGS_DIR / "lists"
ZAPRET_CFGS_BIN_DIR = ZAPRET_CFGS_DIR / "bin"

GITHUB_API_LATEST = "https://api.github.com/repos/bol-van/zapret/releases/latest"
ZAPRET_GIT_URL = "https://github.com/bol-van/zapret"
ZAPRET_CFGS_GIT_URL = "https://github.com/Snowy-Fluffy/zapret.cfgs"

ETC_OS_RELEASE = Path("/etc/os-release")
PROC_MOUNTS = Path("/proc/mounts")

ZAPRETCTL_CONFIG_FILE = ZAPRETCTL_DIR / "config.json"
