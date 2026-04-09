"""Управление конфигурацией zapret."""

import shutil
from pathlib import Path
from typing import List

from .utils import (
    print_output, require_root, get_firewall_type, sha256sum, run_cmd,
    detect_init_system
)
from .constants import (
    ZAPRET_CONFIG_FILE, ZAPRET_HOSTS_USER_FILE, ZAPRET_HOSTS_EXCLUDE_FILE,
    ZAPRET_GAME_IPSET_FILE, ZAPRET_CFGS_CONFIG_DIR, ZAPRET_CFGS_LISTS_DIR,
    ZAPRET_DIR
)
from .service import service_action_cmd

def get_current_config_info() -> dict:
    info = {
        "strategy": "неизвестно",
        "hostlist": "неизвестно",
        "game_mode": False,
        "firewall_type": None
    }
    if ZAPRET_CONFIG_FILE.exists():
        cur_hash = sha256sum(ZAPRET_CONFIG_FILE)
        for cfg_file in ZAPRET_CFGS_CONFIG_DIR.glob("*"):
            if cfg_file.is_file() and sha256sum(cfg_file) == cur_hash:
                info["strategy"] = cfg_file.name
                break
        content = ZAPRET_CONFIG_FILE.read_text()
        import re
        m = re.search(r'^FWTYPE=(\S+)', content, re.MULTILINE)
        if m:
            info["firewall_type"] = m.group(1)
    if ZAPRET_HOSTS_USER_FILE.exists():
        cur_hash = sha256sum(ZAPRET_HOSTS_USER_FILE)
        for lst_file in ZAPRET_CFGS_LISTS_DIR.glob("list*"):
            if lst_file.is_file() and sha256sum(lst_file) == cur_hash:
                info["hostlist"] = lst_file.name
                break
    if ZAPRET_GAME_IPSET_FILE.exists():
        info["game_mode"] = "0.0.0.0/0" in ZAPRET_GAME_IPSET_FILE.read_text()
    return info

def list_strategies() -> List[str]:
    if not ZAPRET_CFGS_CONFIG_DIR.exists():
        return []
    return sorted([f.name for f in ZAPRET_CFGS_CONFIG_DIR.iterdir() if f.is_file()])

def list_hostlists() -> List[str]:
    if not ZAPRET_CFGS_LISTS_DIR.exists():
        return []
    return sorted([f.name for f in ZAPRET_CFGS_LISTS_DIR.glob("list*") if f.is_file()])

def set_strategy(name_or_path: str, no_restart: bool = False):
    require_root()
    src = None
    std = ZAPRET_CFGS_CONFIG_DIR / name_or_path
    if std.exists():
        src = std
    else:
        p = Path(name_or_path)
        if p.exists():
            src = p
    if not src:
        print_output(f"Стратегия не найдена: {name_or_path}", error=True)
        return
    shutil.copy(src, ZAPRET_CONFIG_FILE)
    fw = get_firewall_type()
    content = ZAPRET_CONFIG_FILE.read_text()
    import re
    content = re.sub(r'^FWTYPE=.*', f'FWTYPE={fw}', content, flags=re.MULTILINE)
    ZAPRET_CONFIG_FILE.write_text(content)
    if not no_restart:
        service_action_cmd("restart")
    print_output(f"Стратегия установлена: {src.name}")

def set_hostlist(name_or_path: str, no_restart: bool = False):
    require_root()
    src = None
    std = ZAPRET_CFGS_LISTS_DIR / name_or_path
    if std.exists():
        src = std
    else:
        p = Path(name_or_path)
        if p.exists():
            src = p
    if not src:
        print_output(f"Хостлист не найден: {name_or_path}", error=True)
        return
    shutil.copy(src, ZAPRET_HOSTS_USER_FILE)
    if not no_restart:
        service_action_cmd("restart")
    print_output(f"Хостлист установлен: {src.name}")

def set_game_mode(enable: bool, no_restart: bool = False):
    require_root()
    ZAPRET_GAME_IPSET_FILE.parent.mkdir(parents=True, exist_ok=True)
    if enable:
        ZAPRET_GAME_IPSET_FILE.write_text("0.0.0.0/0\n")
    else:
        ZAPRET_GAME_IPSET_FILE.write_text("203.0.113.77\n")
    if not no_restart:
        service_action_cmd("restart")
    print_output(f"Игровой режим {'включён' if enable else 'выключен'}.")

def set_firewall_type(fw_type: str, no_restart: bool = False):
    require_root()
    if fw_type not in ("iptables", "nftables", "auto"):
        print_output("Допустимые типы: iptables, nftables, auto", error=True)
        return
    if fw_type == "auto":
        fw_type = get_firewall_type()
    content = ZAPRET_CONFIG_FILE.read_text()
    import re
    content = re.sub(r'^FWTYPE=.*', f'FWTYPE={fw_type}', content, flags=re.MULTILINE)
    ZAPRET_CONFIG_FILE.write_text(content)
    if not no_restart:
        service_action_cmd("restart")
    print_output(f"Тип файрвола установлен: {fw_type}")

def edit_file(file_type: str):
    file_map = {
        "strategy": ZAPRET_CONFIG_FILE,
        "hostlist": ZAPRET_HOSTS_USER_FILE,
        "exclude": ZAPRET_HOSTS_EXCLUDE_FILE,
        "custom-strategy": ZAPRET_CFGS_CONFIG_DIR / "conf-custom",
        "custom-hostlist": ZAPRET_CFGS_LISTS_DIR / "list-custom.txt",
    }
    path = file_map.get(file_type)
    if not path:
        print_output(f"Неизвестный тип файла: {file_type}", error=True)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        if file_type == "custom-strategy":
            shutil.copy(ZAPRET_DIR / "config.default", path)
        else:
            path.touch()
    editor = os.environ.get("EDITOR") or os.environ.get("VISUAL") or shutil.which("nano") or shutil.which("vim")
    if not editor:
        print_output("Не найден текстовый редактор.", error=True)
        return
    run_cmd([editor, str(path)], capture=False)
    if file_type in ("strategy", "hostlist", "exclude"):
        service_action_cmd("restart")
        print_output("Сервис перезапущен.")

# Обработчики команд
def cmd_list(args):
    if args.type == "strategies":
        print_output("\n".join(list_strategies()))
    else:
        print_output("\n".join(list_hostlists()))

def cmd_show(args):
    info = get_current_config_info()
    if args.all:
        info["available_strategies"] = list_strategies()
        info["available_hostlists"] = list_hostlists()
    print_output(info)

def cmd_set(args):
    param = args.param
    value = args.value
    no_restart = args.no_restart
    if param == "strategy":
        set_strategy(value, no_restart)
    elif param == "hostlist":
        set_hostlist(value, no_restart)
    elif param == "game-mode":
        enable = value.lower() in ("on", "true", "1", "yes")
        set_game_mode(enable, no_restart)
    elif param == "firewall-type":
        set_firewall_type(value, no_restart)
    else:
        print_output(f"Неизвестный параметр: {param}", error=True)

def cmd_edit(args):
    edit_file(args.file_type)

def load_config_from_file(path: str):
    """Загружает конфигурацию zapretctl из JSON-файла."""
    src = Path(path)
    if not src.exists():
        print_output(f"Файл не найден: {path}", error=True)
        return
    try:
        with open(src, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        print_output(f"Ошибка чтения JSON: {e}", error=True)
        return
    ZAPRETCTL_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(ZAPRETCTL_CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    print_output(f"Конфигурация загружена из {src}")

def save_config_to_file(path: str):
    """Сохраняет текущую конфигурацию zapretctl в JSON-файл."""
    if not ZAPRETCTL_CONFIG_FILE.exists():
        print_output("Файл конфигурации zapretctl не существует.", error=True)
        return
    dst = Path(path)
    try:
        shutil.copy(ZAPRETCTL_CONFIG_FILE, dst)
    except Exception as e:
        print_output(f"Ошибка сохранения: {e}", error=True)
        return
    print_output(f"Конфигурация сохранена в {dst}")

def cmd_up_from_file(args):
    load_config_from_file(args.path)

def cmd_down_to_file(args):
    save_config_to_file(args.path)


