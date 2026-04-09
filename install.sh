#!/bin/sh
set -e

# Установочный скрипт для zapretctl
# Использование:
#   ./install.sh                - установка с sudo (если не root)
#   ./install.sh --sudo doas    - использовать doas вместо sudo
#   ./install.sh --sudo "su -c" - использовать su -c

REPO_URL="https://github.com/TimeStop34/zapretctl.git"
INSTALL_DIR="/opt/zapretctl"
BIN_PATH="/usr/local/bin/zapretctl"

SUDO_CMD=""
if [ "$(id -u)" -ne 0 ]; then
    SUDO_CMD="sudo"
fi

# Обработка аргументов
while [ $# -gt 0 ]; do
    case "$1" in
        --sudo)
            if [ -n "$2" ]; then
                SUDO_CMD="$2"
                shift
            else
                echo "Ошибка: --sudo требует аргумент (например, doas)"
                exit 1
            fi
            ;;
        -h|--help)
            echo "Установщик zapretctl"
            echo "Использование: $0 [--sudo КОМАНДА]"
            echo "  --sudo КОМАНДА   использовать указанную команду для повышения прав (например, doas, su -c)"
            exit 0
            ;;
        *)
            echo "Неизвестный параметр: $1"
            exit 1
            ;;
    esac
    shift
done

# Проверка наличия git
if ! command -v git >/dev/null 2>&1; then
    echo "Ошибка: git не установлен. Установите git и повторите попытку."
    exit 1
fi

# Проверка наличия python3
if ! command -v python3 >/dev/null 2>&1; then
    echo "Ошибка: python3 не установлен. Установите python3 и повторите попытку."
    exit 1
fi

echo "Установка zapretctl из $REPO_URL в $INSTALL_DIR"

# Если директория уже существует, обновляем её
if [ -d "$INSTALL_DIR" ]; then
    echo "Обнаружена существующая установка в $INSTALL_DIR, выполняется обновление..."
    if [ -d "$INSTALL_DIR/.git" ]; then
        cd "$INSTALL_DIR"
        $SUDO_CMD git pull origin main || {
            echo "Не удалось обновить через git pull. Выполняется свежая установка..."
            $SUDO_CMD rm -rf "$INSTALL_DIR"
        }
    else
        echo "Директория не является git-репозиторием, удаляю..."
        $SUDO_CMD rm -rf "$INSTALL_DIR"
    fi
fi

# Клонирование (если директория не существует)
if [ ! -d "$INSTALL_DIR" ]; then
    $SUDO_CMD git clone "$REPO_URL" "$INSTALL_DIR"
fi

# Установка прав на исполнение для главного скрипта
$SUDO_CMD chmod +x "$INSTALL_DIR/zapretctl.py"

# Создание символической ссылки
if [ -e "$BIN_PATH" ] || [ -L "$BIN_PATH" ]; then
    $SUDO_CMD rm -f "$BIN_PATH"
fi
$SUDO_CMD ln -sf "$INSTALL_DIR/zapretctl.py" "$BIN_PATH"

echo "zapretctl успешно установлен в $BIN_PATH"
echo "Проверьте установку, выполнив: zapretctl --help"
