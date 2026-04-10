#!/bin/sh
set -e

REPO_URL="https://github.com/TimeStop34/zapretctl.git"
INSTALL_DIR="/opt/zapretctl"
BIN_PATH="/usr/local/bin/zapretctl"
TEST_BIN_PATH="/usr/local/bin/zapretctl-test"
TEST_SCRIPT="$INSTALL_DIR/zapretctl-test"
RELEASE_FILE="$INSTALL_DIR/test.release"

SUDO_CMD=""
if [ "$(id -u)" -ne 0 ]; then
    SUDO_CMD="sudo"
fi

SELF_TEST_ONLY=0
SKIP_SELF_TEST=0

while [ $# -gt 0 ]; do
    case "$1" in
        --sudo)
            [ -n "$2" ] || { echo "Ошибка: --sudo требует аргумент"; exit 1; }
            SUDO_CMD="$2"
            shift
            ;;
        --self-test-only)
            SELF_TEST_ONLY=1
            ;;
        --skip-self-test)
            SKIP_SELF_TEST=1
            ;;
        -h|--help)
            echo "Установщик zapretctl"
            echo "Использование: $0 [--sudo КОМАНДА] [--self-test-only] [--skip-self-test]"
            exit 0
            ;;
        *)
            echo "Неизвестный параметр: $1"
            exit 1
            ;;
    esac
    shift
done

if ! command -v git >/dev/null 2>&1; then echo "Ошибка: git не установлен."; exit 1; fi
if ! command -v python3 >/dev/null 2>&1; then echo "Ошибка: python3 не установлен."; exit 1; fi

# Клонирование/обновление
if [ $SELF_TEST_ONLY -eq 0 ]; then
    echo "Установка zapretctl из $REPO_URL в $INSTALL_DIR"
    if [ -d "$INSTALL_DIR" ]; then
        echo "Обнаружена существующая установка, обновление..."
        if [ -d "$INSTALL_DIR/.git" ]; then
            cd "$INSTALL_DIR"
            $SUDO_CMD git pull origin main || {
                echo "Не удалось обновить, удаляю и клонирую заново..."
                $SUDO_CMD rm -rf "$INSTALL_DIR"
            }
        else
            $SUDO_CMD rm -rf "$INSTALL_DIR"
        fi
    fi
    if [ ! -d "$INSTALL_DIR" ]; then
        $SUDO_CMD git clone "$REPO_URL" "$INSTALL_DIR"
    fi

    # Установка прав исполнения
    $SUDO_CMD chmod +x "$INSTALL_DIR/zapretctl.py"
    $SUDO_CMD chmod +x "$TEST_SCRIPT"

    # Создание симлинков
    for link in "$BIN_PATH" "$TEST_BIN_PATH"; do
        if [ -e "$link" ] || [ -L "$link" ]; then
            $SUDO_CMD rm -f "$link"
        fi
    done
    $SUDO_CMD ln -sf "$INSTALL_DIR/zapretctl.py" "$BIN_PATH"
    $SUDO_CMD ln -sf "$TEST_SCRIPT" "$TEST_BIN_PATH"
fi

# Функция самотестирования
run_self_test() {
    echo "Запуск самотестирования..."
    if [ ! -x "$TEST_SCRIPT" ]; then
        echo "Ошибка: тестовый скрипт не найден или не исполняемый."
        return 1
    fi

    CURRENT_JSON=$($SUDO_CMD $TEST_SCRIPT --json 2>/dev/null) || {
        echo "Ошибка выполнения тестового скрипта."
        return 1
    }

    if [ ! -f "$RELEASE_FILE" ]; then
        echo "Файл test.release не найден, пропускаем сверку."
        return 0
    fi

    if ! command -v jq >/dev/null 2>&1; then
        echo "jq не установлен, невозможно сравнить JSON. Установите jq для проверки."
        return 0
    fi

    CURRENT_NORM=$(echo "$CURRENT_JSON" | jq --sort-keys .)
    RELEASE_NORM=$(jq --sort-keys . "$RELEASE_FILE")

    if [ "$CURRENT_NORM" = "$RELEASE_NORM" ]; then
        echo "✅ Самотестирование пройдено: вывод совпадает с test.release."
        return 0
    else
        echo "❌ Ошибка: вывод теста не совпадает с test.release!"
        echo "Различия:"
        diff <(echo "$CURRENT_NORM") <(echo "$RELEASE_NORM") || true
        return 1
    fi
}

if [ $SELF_TEST_ONLY -eq 1 ]; then
    run_self_test
    exit $?
fi

if [ $SKIP_SELF_TEST -eq 0 ]; then
    if ! run_self_test; then
        echo ""
        echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
        echo "ВНИМАНИЕ: Самотестирование выявило расхождения."
        echo "Установка прервана. Проверьте целостность репозитория."
        echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
        exit 1
    fi
fi

echo "zapretctl успешно установлен в $BIN_PATH"
echo "zapretctl-test успешно установлен в $TEST_BIN_PATH"
echo "Проверьте: zapretctl --help"
