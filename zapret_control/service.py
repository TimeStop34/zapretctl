"""Управление сервисом zapret."""

import shutil
from pathlib import Path

from .utils import run_cmd, print_output, require_root, detect_init_system
from .constants import ZAPRET_DIR

def service_action_cmd(action: str):
    init = detect_init_system()
    require_root()
    if init == "systemd":
        cmd = ["systemctl", action, "zapret"]
    elif init == "openrc":
        cmd = ["rc-service", "zapret", action]
    elif init in ("runit", "runit-artix"):
        cmd = ["sv", action, "zapret"]
    elif init in ("sysvinit", "procd"):
        cmd = ["service", "zapret", action]
    else:
        print_output(f"Неизвестная init-система: {init}", error=True)
        return
    if action == "status":
        code, out, err = run_cmd(cmd, check=False)
        if code == 0:
            print_output(out or "Сервис работает")
        else:
            print_output(err or "Сервис не работает", error=True)
    else:
        run_cmd(cmd, check=True)
        print_output(f"Сервис: {action} выполнен.")

def service_enable(enable: bool):
    init = detect_init_system()
    require_root()
    if init == "systemd":
        action = "enable" if enable else "disable"
        run_cmd(["systemctl", action, "zapret"], check=True)
    elif init == "runit":
        sv_dir = Path("/var/service/zapret")
        src = ZAPRET_DIR / "init.d" / "runit" / "zapret"
        if enable:
            if not sv_dir.exists():
                sv_dir.symlink_to(src)
        else:
            sv_dir.unlink(missing_ok=True)
    elif init == "runit-artix":
        sv_dir = Path("/run/runit/service/zapret")
        src = ZAPRET_DIR / "init.d" / "runit" / "zapret"
        if enable:
            if not sv_dir.exists():
                sv_dir.symlink_to(src)
        else:
            sv_dir.unlink(missing_ok=True)
    elif init == "sysvinit":
        if enable:
            run_cmd(["update-rc.d", "zapret", "defaults"], check=True)
        else:
            run_cmd(["update-rc.d", "-f", "zapret", "remove"], check=True)
    elif init == "openrc":
        if enable:
            run_cmd(["rc-update", "add", "zapret", "default"], check=True)
        else:
            run_cmd(["rc-update", "del", "zapret"], check=True)
    elif init == "procd":
        action = "enable" if enable else "disable"
        run_cmd(["service", "zapret", action], check=True)
    else:
        print_output(f"Автозапуск не поддерживается для {init}", error=True)
        return
    print_output(f"Автозапуск {'включён' if enable else 'выключен'}.")

def get_service_status() -> dict:
    init = detect_init_system()
    active = False
    enabled = False
    if init == "systemd":
        code, _, _ = run_cmd(["systemctl", "is-active", "zapret"], check=False)
        active = (code == 0)
        code, _, _ = run_cmd(["systemctl", "is-enabled", "zapret"], check=False)
        enabled = (code == 0)
    elif init == "openrc":
        code, _, _ = run_cmd(["rc-service", "zapret", "status"], check=False)
        active = (code == 0)
        _, out, _ = run_cmd(["rc-update", "show"], check=False)
        enabled = "zapret" in out
    elif init == "procd":
        _, out, _ = run_cmd(["/etc/init.d/zapret", "status"], check=False)
        active = "running" in out
        enabled = bool(list(Path("/etc/rc.d").glob("S*zapret*")))
    elif init in ("runit", "runit-artix"):
        sv_dir = Path("/var/service") if init == "runit" else Path("/run/runit/service")
        _, out, _ = run_cmd(["sv", "status", "zapret"], check=False)
        active = "run" in out
        enabled = (sv_dir / "zapret").exists()
    elif init == "sysvinit":
        code, _, _ = run_cmd(["service", "zapret", "status"], check=False)
        active = (code == 0)
        enabled = Path("/etc/init.d/zapret").exists()
    return {"active": active, "enabled": enabled}

# Обработчики команд
def cmd_start(args):
    service_action_cmd("start")

def cmd_stop(args):
    service_action_cmd("stop")

def cmd_restart(args):
    service_action_cmd("restart")

def cmd_status(args):
    service_action_cmd("status")

def cmd_enable(args):
    service_enable(True)

def cmd_disable(args):
    service_enable(False)
