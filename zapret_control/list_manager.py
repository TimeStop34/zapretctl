"""Управление списками hosts и exclude."""

from .utils import print_output, require_root, parse_address_list
from .constants import ZAPRET_HOSTS_USER_FILE, ZAPRET_HOSTS_EXCLUDE_FILE
from .service import service_action_cmd

def _get_list_file(list_type: str):
    if list_type == "hosts":
        return ZAPRET_HOSTS_USER_FILE
    elif list_type == "exclude":
        return ZAPRET_HOSTS_EXCLUDE_FILE
    else:
        print_output(f"Неизвестный тип списка: {list_type}", error=True)

def add_entries(list_type: str, addresses, no_restart: bool = False):
    require_root()
    list_file = _get_list_file(list_type)
    list_file.parent.mkdir(parents=True, exist_ok=True)
    existing = set()
    if list_file.exists():
        existing = set(list_file.read_text().splitlines())
    added = []
    for addr in addresses:
        addr = addr.strip()
        if addr and addr not in existing:
            existing.add(addr)
            added.append(addr)
    if added:
        list_file.write_text("\n".join(sorted(existing)) + "\n")
        print_output(f"Добавлено в {list_type}: {', '.join(added)}")
        if not no_restart:
            service_action_cmd("restart")
    else:
        print_output("Нет новых адресов для добавления.")

def remove_entries(list_type: str, addresses, no_restart: bool = False):
    require_root()
    list_file = _get_list_file(list_type)
    if not list_file.exists():
        print_output(f"Список {list_type} пуст или не существует.", error=True)
        return
    lines = list_file.read_text().splitlines()
    remove_set = set(addresses)
    new_lines = [l for l in lines if l.strip() not in remove_set]
    removed = set(lines) - set(new_lines)
    if removed:
        list_file.write_text("\n".join(new_lines) + "\n")
        print_output(f"Удалено из {list_type}: {', '.join(removed)}")
        if not no_restart:
            service_action_cmd("restart")
    else:
        print_output("Указанные адреса не найдены.")

def search_entries(list_type: str, keyword: str):
    list_file = _get_list_file(list_type)
    if not list_file.exists():
        print_output(f"Список {list_type} пуст.")
        return
    matches = [line.strip() for line in list_file.read_text().splitlines() if keyword.lower() in line.lower()]
    if matches:
        print_output("\n".join(matches))
    else:
        print_output("Совпадений не найдено.")

def show_entries(list_type: str):
    list_file = _get_list_file(list_type)
    if not list_file.exists():
        print_output(f"Список {list_type} пуст.")
        return
    print_output(list_file.read_text())

# Обработчики
def cmd_add(args):
    add_entries(args.list_type, args.addresses, args.no_restart)

def cmd_remove(args):
    remove_entries(args.list_type, args.addresses, args.no_restart)

def cmd_search(args):
    search_entries(args.list_type, args.keyword)

def cmd_show(args):
    show_entries(args.list_type)
