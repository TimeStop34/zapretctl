"""Парсер аргументов и диспетчер."""

import argparse
import sys

from . import __version__
from .utils import set_json_output, print_output
from . import general, install, service, config_manager, list_manager, checker, debug

def create_parser():
    parser = argparse.ArgumentParser(
        prog="zapretctl",
        description="Управление Zapret из командной строки"
    )
    parser.add_argument("--json", action="store_true", help="Вывод в формате JSON")
    parser.add_argument("-v", "--version", action="version", version=f"zapretctl {__version__}")
    subparsers = parser.add_subparsers(dest="object", required=False)

    # general
    gen_parser = subparsers.add_parser("general", help="Общая информация")
    gen_sub = gen_parser.add_subparsers(dest="action", required=True)
    gen_sub.add_parser("status")
    gen_sub.add_parser("version")

    # install
    inst_parser = subparsers.add_parser("install", help="Установка, обновление, удаление")
    inst_sub = inst_parser.add_subparsers(dest="action", required=True)
    inst_install = inst_sub.add_parser("install")
    inst_install.add_argument("--release", dest="method", action="store_const", const="release", default="release")
    inst_install.add_argument("--git", dest="method", action="store_const", const="git")
    inst_install.add_argument("--force", action="store_true")
    inst_update = inst_sub.add_parser("update")
    inst_update.add_argument("--full", action="store_true", default=True)
    inst_update.add_argument("--script-only", dest="full", action="store_false")
    inst_uninstall = inst_sub.add_parser("uninstall")
    inst_uninstall.add_argument("--force", action="store_true")

    # service
    svc_parser = subparsers.add_parser("service")
    svc_sub = svc_parser.add_subparsers(dest="action", required=True)
    svc_sub.add_parser("start")
    svc_sub.add_parser("stop")
    svc_sub.add_parser("restart")
    svc_sub.add_parser("status")
    svc_sub.add_parser("enable")
    svc_sub.add_parser("disable")

    # config
    cfg_parser = subparsers.add_parser("config")
    cfg_sub = cfg_parser.add_subparsers(dest="action", required=True)
    cfg_list = cfg_sub.add_parser("list")
    cfg_list.add_argument("type", choices=["strategies", "hostlists"])
    cfg_show = cfg_sub.add_parser("show")
    cfg_show.add_argument("--all", action="store_true")
    cfg_set = cfg_sub.add_parser("set")
    cfg_set.add_argument("param", choices=["strategy", "hostlist", "game-mode", "firewall-type"])
    cfg_set.add_argument("value")
    cfg_set.add_argument("--no-restart", action="store_true")
    cfg_edit = cfg_sub.add_parser("edit")
    cfg_edit.add_argument("file_type", choices=["strategy", "hostlist", "exclude", "custom-strategy", "custom-hostlist"])
    cfg_up = cfg_sub.add_parser("up-from-file", help="Загрузить конфигурацию zapretctl из JSON-файла")
    cfg_up.add_argument("path", help="Путь к JSON-файлу")
    cfg_down = cfg_sub.add_parser("down-to-file", help="Сохранить конфигурацию zapretctl в JSON-файл")
    cfg_down.add_argument("path", help="Путь для сохранения")


    # list
    lst_parser = subparsers.add_parser("list")
    lst_sub = lst_parser.add_subparsers(dest="action", required=True)
    lst_add = lst_sub.add_parser("add")
    lst_add.add_argument("list_type", choices=["hosts", "exclude"])
    lst_add.add_argument("addresses", nargs="+")
    lst_add.add_argument("--no-restart", action="store_true")
    lst_remove = lst_sub.add_parser("remove")
    lst_remove.add_argument("list_type", choices=["hosts", "exclude"])
    lst_remove.add_argument("addresses", nargs="+")
    lst_remove.add_argument("--no-restart", action="store_true")
    lst_search = lst_sub.add_parser("search")
    lst_search.add_argument("list_type", choices=["hosts", "exclude"])
    lst_search.add_argument("keyword")
    lst_show = lst_sub.add_parser("show")
    lst_show.add_argument("list_type", choices=["hosts", "exclude"])

    # check
    chk_parser = subparsers.add_parser("check")
    chk_sub = chk_parser.add_subparsers(dest="action", required=True)
    chk_run = chk_sub.add_parser("run")
    chk_run.add_argument("--hostlist")
    chk_run.add_argument("--strategies", nargs="+")
    chk_run.add_argument("--all-strategies", action="store_true")
    chk_run.add_argument("--apply-best", action="store_true")
    chk_domain = chk_sub.add_parser("domain")
    chk_domain.add_argument("domain")
    chk_domain.add_argument("--strategy")

    # debug
    dbg_parser = subparsers.add_parser("debug")
    dbg_sub = dbg_parser.add_subparsers(dest="action", required=True)
    dbg_sub.add_parser("init-info")
    dbg_sub.add_parser("dump-state")

    return parser

def main():
    parser = create_parser()
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)
    args = parser.parse_args()
    set_json_output(args.json)

    # Диспетчеризация
    if args.object == "general":
        if args.action == "status":
            general.cmd_status(args)
        elif args.action == "version":
            general.cmd_version(args)
    elif args.object == "install":
        if args.action == "install":
            install.cmd_install(args)
        elif args.action == "update":
            install.cmd_update(args)
        elif args.action == "uninstall":
            install.cmd_uninstall(args)
    elif args.object == "service":
        action = args.action
        if action == "start":
            service.cmd_start(args)
        elif action == "stop":
            service.cmd_stop(args)
        elif action == "restart":
            service.cmd_restart(args)
        elif action == "status":
            service.cmd_status(args)
        elif action == "enable":
            service.cmd_enable(args)
        elif action == "disable":
            service.cmd_disable(args)
    elif args.object == "config":
        if args.action == "list":
            config_manager.cmd_list(args)
        elif args.action == "show":
            config_manager.cmd_show(args)
        elif args.action == "set":
            config_manager.cmd_set(args)
        elif args.action == "edit":
            config_manager.cmd_edit(args)
        elif args.action == "up-from-file":
            config_manager.cmd_up_from_file(args)
        elif args.action == "down-to-file":
             config_manager.cmd_down_to_file(args)
    elif args.object == "list":
        if args.action == "add":
            list_manager.cmd_add(args)
        elif args.action == "remove":
            list_manager.cmd_remove(args)
        elif args.action == "search":
            list_manager.cmd_search(args)
        elif args.action == "show":
            list_manager.cmd_show(args)
    elif args.object == "check":
        if args.action == "run":
            checker.cmd_run(args)
        elif args.action == "domain":
            checker.cmd_domain(args)
    elif args.object == "debug":
        if args.action == "init-info":
            debug.cmd_init_info(args)
        elif args.action == "dump-state":
            debug.cmd_dump_state(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
