"""Объект general - статус и версия."""

from .utils import print_output, is_zapret_installed, get_current_version
from .service import get_service_status
from .config_manager import get_current_config_info
from . import __version__

def cmd_status(args):
    installed = is_zapret_installed()
    info = {"installed": installed}
    if installed:
        info.update(get_service_status())
        info.update(get_current_config_info())
        info["version"] = get_current_version()
    print_output(info)

def cmd_version(args):
    from .install import get_latest_version
    installed = is_zapret_installed()
    current = get_current_version()
    latest = get_latest_version()
    info = {
        "zapret_installed": installed,
        "current_version": current,
        "latest_version": latest,
        "zapretctl_version": __version__
    }
    print_output(info)
