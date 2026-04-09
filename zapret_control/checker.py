"""Проверка доступности и подбор стратегий."""

import time
from pathlib import Path

from .utils import run_cmd, print_output, is_ip_address
from .config_manager import set_strategy, set_hostlist, list_strategies, get_current_config_info
from .constants import ZAPRET_HOSTS_USER_FILE
from .service import service_action_cmd

def test_domain(domain: str) -> dict:
    res = {"domain": domain, "ping": None, "http": None, "tls12": None, "tls13": None}
    if is_ip_address(domain):
        code, out, _ = run_cmd(["ping", "-c", "2", "-W", "2", domain], check=False)
        if code == 0:
            import re
            m = re.search(r"rtt min/avg/max/mdev = [\d.]+/([\d.]+)/", out)
            res["ping"] = f"{m.group(1)}ms" if m else "OK"
        else:
            res["ping"] = "FAIL"
    else:
        code, out, _ = run_cmd(["ping", "-c", "2", "-W", "2", domain], check=False)
        if code == 0:
            import re
            m = re.search(r"rtt min/avg/max/mdev = [\d.]+/([\d.]+)/", out)
            res["ping"] = f"{m.group(1)}ms" if m else "OK"
        else:
            res["ping"] = "FAIL"
        # HTTP
        code, out, _ = run_cmd(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", f"http://{domain}"],
                               check=False, timeout=5)
        res["http"] = f"HTTP:{out}" if code == 0 and out.isdigit() else "FAIL"
        # TLS1.2
        code, out, _ = run_cmd(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "--tlsv1.2", f"https://{domain}"],
                               check=False, timeout=5)
        res["tls12"] = f"TLS1.2:{out}" if code == 0 and out.isdigit() else "FAIL"
        # TLS1.3
        code, out, _ = run_cmd(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "--tlsv1.3", f"https://{domain}"],
                               check=False, timeout=5)
        res["tls13"] = f"TLS1.3:{out}" if code == 0 and out.isdigit() else "FAIL"
    return res

def run_check(args):
    if args.hostlist:
        set_hostlist(args.hostlist, no_restart=True)
    if args.all_strategies:
        strategies = list_strategies()
    elif args.strategies:
        strategies = args.strategies
    else:
        print_output("Укажите стратегии или --all-strategies", error=True)
        return
    hostlist_path = ZAPRET_HOSTS_USER_FILE
    if not hostlist_path.exists():
        print_output("Хостлист не найден.", error=True)
        return
    domains = [line.strip() for line in hostlist_path.read_text().splitlines() if line.strip() and not line.startswith("#")]
    total = len(domains)
    print(f"Проверка {len(strategies)} стратегий на {total} доменах...")
    best = {"name": None, "available": -1}
    for strat in strategies:
        set_strategy(strat, no_restart=True)
        service_action_cmd("restart")
        time.sleep(2)
        available = 0
        for dom in domains:
            res = test_domain(dom)
            if is_ip_address(dom):
                if res["ping"] != "FAIL":
                    available += 1
            else:
                if res["tls12"] != "FAIL" or res["tls13"] != "FAIL":
                    available += 1
        print(f"Стратегия {strat}: {available}/{total}")
        if available > best["available"]:
            best = {"name": strat, "available": available}
    if best["name"]:
        print(f"\nЛучшая стратегия: {best['name']} ({best['available']}/{total})")
        if args.apply_best:
            set_strategy(best["name"])
    else:
        print("Не удалось определить лучшую стратегию.")

def cmd_run(args):
    run_check(args)

def cmd_domain(args):
    if args.strategy:
        # Временно применить стратегию для теста (без сохранения?)
        current = get_current_config_info()["strategy"]
        set_strategy(args.strategy, no_restart=True)
        service_action_cmd("restart")
        time.sleep(2)
    res = test_domain(args.domain)
    print_output(res)
    if args.strategy:
        set_strategy(current, no_restart=True)
        service_action_cmd("restart")
