"""Отладочные команды."""

from .utils import print_output, detect_init_system, get_os_info, get_firewall_type, is_openwrt, is_zapret_installed
from .config_manager import get_current_config_info
from .service import get_service_status

def cmd_init_info(args):
    info = {
        "init": detect_init_system(),
        "os": get_os_info(),
        "firewall_type": get_firewall_type(),
        "openwrt": is_openwrt(),
        "zapret_installed": is_zapret_installed(),
    }
    print_output(info)

def cmd_dump_state(args):
    info = {
        "init": detect_init_system(),
        "os": get_os_info(),
        "firewall_type": get_firewall_type(),
        "zapret_installed": is_zapret_installed(),
    }
    if is_zapret_installed():
        info["service"] = get_service_status()
        info["config"] = get_current_config_info()
    print_output(info)
