#!/bin/bash
# zapretctl test suite - проверка всех команд zapretctl

PASS=0
FAIL=0
SKIP=0

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

run_test() {
    local description="$1"
    local cmd="$2"
    local need_root="$3"

    echo -n "Тест: $description ... "

    if [[ "$need_root" == "yes" ]] && [[ $EUID -ne 0 ]]; then
        if command -v sudo &>/dev/null; then
            cmd="sudo $cmd"
        elif command -v doas &>/dev/null; then
            cmd="doas $cmd"
        else
            echo -e "${YELLOW}SKIP${NC} (требуется root, но sudo/doas не найден)"
            ((SKIP++))
            return
        fi
    fi

    # Выполняем команду, игнорируем stdout/stderr, сохраняем код возврата
    if eval "$cmd" &>/dev/null; then
        echo -e "${GREEN}PASS${NC}"
        ((PASS++))
    else
        echo -e "${RED}FAIL${NC} (код $?)"
        echo "  Команда: $cmd"
        ((FAIL++))
    fi
}

echo "========================================="
echo "   Тестирование zapretctl CLI"
echo "========================================="

if ! command -v zapretctl &>/dev/null; then
    echo -e "${RED}Ошибка: zapretctl не найден в PATH${NC}"
    exit 1
fi

# Базовые
run_test "zapretctl --help" "zapretctl --help" "no"
run_test "zapretctl --version" "zapretctl --version" "no"
run_test "zapretctl --json general version" "zapretctl --json general version" "no"

# general
run_test "general status" "zapretctl general status" "no"
run_test "general version" "zapretctl general version" "no"

# service
run_test "service status" "zapretctl service status" "yes"
run_test "service start" "zapretctl service start" "yes"
run_test "service stop" "zapretctl service stop" "yes"
run_test "service restart" "zapretctl service restart" "yes"
run_test "service enable" "zapretctl service enable" "yes"
run_test "service disable" "zapretctl service disable" "yes"

# config
run_test "config list strategies" "zapretctl config list strategies" "no"
run_test "config list hostlists" "zapretctl config list hostlists" "no"
run_test "config show" "zapretctl config show" "no"
run_test "config show --all" "zapretctl config show --all" "no"
run_test "config set strategy general" "zapretctl config set strategy general" "yes"
run_test "config set game-mode off" "zapretctl config set game-mode off" "yes"
#run_test "config edit strategy (help)" "zapretctl config edit strategy" "no"
run_test "config up-from-file /dev/null" "zapretctl config up-from-file <<< '{}'" "no"
run_test "config down-to-file /tmp/zapret-test.json" "zapretctl config down-to-file /tmp/zapret-test.json" "yes"
rm -f /tmp/zapret-test.json

# list
run_test "list show hosts" "zapretctl list show hosts" "no"
run_test "list show exclude" "zapretctl list show exclude" "no"
run_test "list search hosts google" "zapretctl list search hosts google" "no"
run_test "list add hosts test.local --no-restart" "zapretctl list add hosts test.local --no-restart" "yes"
run_test "list remove hosts test.local --no-restart" "zapretctl list remove hosts test.local --no-restart" "yes"

# check
run_test "check run --help" "zapretctl check run --help" "no"
run_test "check domain --help" "zapretctl check domain --help" "no"

# debug
run_test "debug init-info" "zapretctl debug init-info" "no"
run_test "debug dump-state" "zapretctl debug dump-state" "no"

# install
run_test "install --help" "zapretctl install --help" "no"
run_test "install install --help" "zapretctl install install --help" "no"
run_test "install update --help" "zapretctl install update --help" "no"
run_test "install uninstall --help" "zapretctl install uninstall --help" "no"

echo "========================================="
echo -e "Результаты: ${GREEN}Пройдено $PASS${NC}, ${RED}Провалено $FAIL${NC}, ${YELLOW}Пропущено $SKIP${NC}"
echo "========================================="

if [[ $FAIL -gt 0 ]]; then
    exit 1
else
    exit 0
fi
