"""Установка, обновление, удаление zapret."""

import json
import re
import shutil
import tempfile
import urllib.request
from pathlib import Path

from .utils import (
    run_cmd, print_output, require_root, is_openwrt, detect_init_system,
    get_firewall_type, is_zapret_installed, get_current_version
)
from .constants import (
    ZAPRET_DIR, ZAPRET_VERSION_FILE, GITHUB_API_LATEST, ZAPRET_GIT_URL,
    ZAPRET_CFGS_GIT_URL, ZAPRET_CFGS_DIR, ZAPRET_CFGS_CONFIG_DIR,
    ZAPRET_CFGS_LISTS_DIR, ZAPRET_CFGS_BIN_DIR, ZAPRETCTL_DIR,
    ZAPRET_CONFIG_FILE, ZAPRET_HOSTS_USER_FILE, ZAPRET_HOSTS_EXCLUDE_FILE,
    ZAPRET_GAME_IPSET_FILE
)
from .service import service_action_cmd
from .config_manager import set_strategy, set_hostlist

def get_latest_version():
    try:
        with urllib.request.urlopen(GITHUB_API_LATEST, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            tag = data.get("tag_name", "")
            if tag.startswith("v"):
                return tag[1:]
            return tag
    except Exception:
        return None

def download_zapret_release(version: str):
    shutil.rmtree(ZAPRET_DIR, ignore_errors=True)
    ZAPRET_DIR.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(GITHUB_API_LATEST) as resp:
        data = json.loads(resp.read().decode())
    assets = data.get('assets', [])
    if is_openwrt():
        asset = next((a for a in assets if 'openwrt' in a['name'].lower()), None)
    else:
        asset = next((a for a in assets if 'openwrt' not in a['name'].lower()), None)
    if not asset:
        print_output("Не найден подходящий архив релиза.", error=True)
        return
    url = asset['browser_download_url']
    with tempfile.TemporaryDirectory() as tmpdir:
        archive = Path(tmpdir) / "zapret.tar.gz"
        urllib.request.urlretrieve(url, archive)
        shutil.unpack_archive(archive, ZAPRET_DIR)
    ZAPRET_VERSION_FILE.write_text(version + "\n")

def download_zapret_git():
    shutil.rmtree(ZAPRET_DIR, ignore_errors=True)
    run_cmd(["git", "clone", ZAPRET_GIT_URL, str(ZAPRET_DIR)], check=True)
    ZAPRET_VERSION_FILE.write_text("git\n")

def clone_configs_repo():
    if ZAPRET_CFGS_DIR.exists():
        shutil.rmtree(ZAPRET_CFGS_DIR)
    run_cmd(["git", "clone", ZAPRET_CFGS_GIT_URL, str(ZAPRET_CFGS_DIR)], check=True)

def run_install_easy():
    installer = ZAPRET_DIR / "install_easy.sh"
    if not installer.exists():
        print_output("install_easy.sh не найден.", error=True)
        return
    common_installer = ZAPRET_DIR / "common" / "installer.sh"
    if common_installer.exists():
        content = common_installer.read_text()
        content = content.replace('ask_yes_no N', 'ask_yes_no Y')
        common_installer.write_text(content)
    run_cmd(["bash", "-c", f"yes | {installer}"], check=True, capture=False)
    if common_installer.exists():
        content = common_installer.read_text().replace('ask_yes_no Y', 'ask_yes_no N')
        common_installer.write_text(content)

def post_install_setup():
    # Копирование дефолтных конфигов
    general_cfg = ZAPRET_CFGS_CONFIG_DIR / "general"
    if general_cfg.exists():
        shutil.copy(general_cfg, ZAPRET_CONFIG_FILE)
        # Установка типа файрвола
        fw = get_firewall_type()
        content = ZAPRET_CONFIG_FILE.read_text()
        content = re.sub(r'^FWTYPE=.*', f'FWTYPE={fw}', content, flags=re.MULTILINE)
        ZAPRET_CONFIG_FILE.write_text(content)
    fake_src = ZAPRET_CFGS_BIN_DIR
    fake_dst = ZAPRET_DIR / "files" / "fake"
    if fake_src.exists():
        shutil.copytree(fake_src, fake_dst, dirs_exist_ok=True)
    basic_list = ZAPRET_CFGS_LISTS_DIR / "list-basic.txt"
    ZAPRET_HOSTS_USER_FILE.parent.mkdir(parents=True, exist_ok=True)
    if basic_list.exists():
        shutil.copy(basic_list, ZAPRET_HOSTS_USER_FILE)
    ZAPRET_HOSTS_EXCLUDE_FILE.parent.mkdir(parents=True, exist_ok=True)
    ZAPRET_HOSTS_EXCLUDE_FILE.touch()
    ZAPRET_GAME_IPSET_FILE.parent.mkdir(parents=True, exist_ok=True)
    ZAPRET_GAME_IPSET_FILE.write_text("203.0.113.77\n")
    # Симлинк zapretctl
    zapretctl_bin = Path("/usr/local/bin/zapretctl")
    if not zapretctl_bin.exists():
        zapretctl_bin.symlink_to(ZAPRETCTL_DIR / "zapretctl.py")
    if detect_init_system() == "systemd":
        run_cmd(["systemctl", "daemon-reload"])
    # Предупреждение для runit
    if detect_init_system() in ("runit", "runit-artix"):
        print_output("Рекомендуется перезагрузить систему для корректной работы runit.")

def install_zapret(method: str = "release", force: bool = False):
    require_root()
    if is_zapret_installed() and not force:
        print_output("Zapret уже установлен. Используйте --force для переустановки.", error=True)
        return
    if method == "release":
        version = get_latest_version()
        if not version:
            print_output("Не удалось получить последнюю версию.", error=True)
            return
        download_zapret_release(version)
    else:
        download_zapret_git()
    clone_configs_repo()
    run_install_easy()
    post_install_setup()
    set_strategy("general")
    set_hostlist("list-basic.txt")
    service_action_cmd("restart")
    print_output("Zapret успешно установлен.")

def update_zapret(full: bool = True):
    require_root()
    if not is_zapret_installed():
        print_output("Zapret не установлен.", error=True)
        return
    if full:
        ver = get_current_version()
        if ver and ver != "git":
            version = get_latest_version()
            if version and version != ver:
                download_zapret_release(version)
                run_install_easy()
        else:
            run_cmd(["git", "-C", str(ZAPRET_DIR), "pull"], check=True)
            run_install_easy()
    # Обновление конфигураций
    if ZAPRET_CFGS_DIR.exists():
        run_cmd(["git", "-C", str(ZAPRET_CFGS_DIR), "pull"], check=True)
    # Обновление zapretctl (если установлен через git)
    if (ZAPRETCTL_DIR / ".git").exists():
        run_cmd(["git", "-C", str(ZAPRETCTL_DIR), "pull"], check=True)
    post_install_setup()
    service_action_cmd("restart")
    print_output("Обновление завершено.")

def uninstall_zapret(force: bool = False):
    require_root()
    if not force:
        ans = input("Вы уверены, что хотите удалить zapret? (y/N) ").strip().lower()
        if ans != 'y':
            return
    uninstaller = ZAPRET_DIR / "uninstall_easy.sh"
    if uninstaller.exists():
        run_cmd(["yes", "|", str(uninstaller)], check=False)
    shutil.rmtree(ZAPRET_DIR, ignore_errors=True)
    shutil.rmtree(ZAPRET_INSTALLER_DIR, ignore_errors=True)
    ZAPRET_VERSION_FILE.unlink(missing_ok=True)
    Path("/usr/local/bin/zapretctl").unlink(missing_ok=True)
    print_output("Zapret удалён.")

# Обработчики команд
def cmd_install(args):
    method = args.method or "release"
    install_zapret(method, args.force)

def cmd_update(args):
    update_zapret(full=args.full)

def cmd_uninstall(args):
    uninstall_zapret(args.force)
