# Деплой на Railway.app с PostgreSQL

Полная инструкция по развертыванию Telegram бота на Railway.app с использованием PostgreSQL базы данных.

## Предварительные требования

1. **GitHub аккаунт** - для подключения репозитория
2. **Telegram Bot Token** - получить у [@BotFather](https://t.me/BotFather)
3. **Telegram ID лидера клана** - получить у [@userinfobot](https://t.me/userinfobot)

## Шаг 1: Подготовка репозитория

Убедитесь, что ваш код запушен в GitHub:

\`\`\`bash
git add .
git commit -m "feat: готов к деплою на Railway"
git push origin main
\`\`\`

## Шаг 2: Регистрация на Railway.app

1. Перейдите на [railway.app](https://railway.app)
2. Нажмите **Login** и войдите через GitHub
3. Подтвердите доступ Railway к вашим репозиториям

## Шаг 3: Создание нового проекта

1. В Railway Dashboard нажмите **New Project**
2. Выберите **Deploy from GitHub repo**
3. Выберите репозиторий \`clan-bot\`
4. Railway автоматически определит Dockerfile и начнет сборку

## Шаг 4: Добавление PostgreSQL

1. В проекте нажмите **New** → **Database** → **Add PostgreSQL**
2. Railway автоматически создаст PostgreSQL сервис
3. Переменная \`DATABASE_URL\` будет создана автоматически

## Дополнительная информация

Полная документация доступна в README.md
