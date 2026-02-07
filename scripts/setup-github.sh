#!/bin/bash

# Скрипт для быстрой настройки GitHub репозитория
# Использование: ./scripts/setup-github.sh YOUR_USERNAME REPO_NAME

set -e

if [ $# -lt 2 ]; then
    echo "Использование: $0 <github_username> <repo_name>"
    echo "Пример: $0 myusername ProjectUnicorn"
    exit 1
fi

USERNAME=$1
REPO_NAME=$2

echo "🚀 Настройка GitHub репозитория..."
echo "Username: $USERNAME"
echo "Repository: $REPO_NAME"

# Проверка инициализации Git
if [ ! -d .git ]; then
    echo "📦 Инициализация Git репозитория..."
    git init
fi

# Добавление remote (если еще не добавлен)
if git remote get-url origin >/dev/null 2>&1; then
    echo "⚠️  Remote 'origin' уже настроен"
    read -p "Хотите обновить? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git remote set-url origin "https://github.com/$USERNAME/$REPO_NAME.git"
    fi
else
    echo "🔗 Добавление remote репозитория..."
    git remote add origin "https://github.com/$USERNAME/$REPO_NAME.git"
fi

# Проверка наличия коммитов
if ! git rev-parse --verify HEAD >/dev/null 2>&1; then
    echo "📝 Создание первого коммита..."
    git add .
    git commit -m "Initial commit: Project structure setup"
fi

# Переименование ветки в main (если нужно)
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo "🔄 Переименование ветки в main..."
    git branch -M main
fi

echo ""
echo "✅ Настройка завершена!"
echo ""
echo "Следующие шаги:"
echo "1. Убедитесь, что репозиторий $REPO_NAME создан на GitHub"
echo "2. Выполните: git push -u origin main"
echo ""
echo "Для создания первого релиза:"
echo "  git tag -a v1.0.0 -m 'Release version 1.0.0'"
echo "  git push origin v1.0.0"
