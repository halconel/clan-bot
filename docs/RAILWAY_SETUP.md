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
4. **Важно**: Railway создает DATABASE_URL в формате \`postgresql://...\`, но нашему боту нужен формат \`postgresql+asyncpg://...\`

## Шаг 5: Настройка переменных окружения

1. Перейдите в сервис бота → **Variables**
2. Добавьте следующие переменные:

\`\`\`bash
# Telegram Bot Configuration
BOT_TOKEN=ваш_токен_от_BotFather
LEADER_TELEGRAM_ID=ваш_telegram_id

# Database (PostgreSQL создает автоматически, но нужно исправить формат)
# Найдите переменную DATABASE_URL и измените префикс:
# Было: postgresql://user:pass@host:port/db
# Нужно: postgresql+asyncpg://user:pass@host:port/db

# Storage Configuration
SCREENSHOTS_DIR=data/screenshots
TEMP_STORAGE_FILE=data/pending.json

# Logging
LOG_LEVEL=INFO
LOG_FILE=bot.log
\`\`\`

**Как исправить DATABASE_URL:**
1. Скопируйте значение переменной DATABASE_URL
2. Измените \`postgresql://\` на \`postgresql+asyncpg://\`
3. Сохраните изменения

Пример:
- До: \`postgresql://postgres:pass@host.railway.app:5432/railway\`
- После: \`postgresql+asyncpg://postgres:pass@host.railway.app:5432/railway\`

## Шаг 6: Настройка Deploy Branch

1. Перейдите в Settings → **Source**
2. В поле **Deploy Branch** выберите \`main\`
3. Включите **Auto-Deploy** (автоматический деплой при push в main)

## Шаг 7: Добавление Volume для данных

1. В сервисе бота перейдите в Settings → **Volumes**
2. Нажмите **New Volume**
3. Mount Path: \`/app/data\`
4. Это сохранит скриншоты между перезапусками

## Шаг 8: Первый деплой

1. Railway автоматически начнет сборку после добавления переменных
2. Проверьте логи: перейдите в сервис бота → **Deployments** → последний деплой → **View Logs**
3. Дождитесь сообщений:
   \`\`\`
   Loading settings...
   Initializing database...
   Database tables created/verified
   Initializing bot...
   Starting bot polling...
   \`\`\`

## Шаг 9: Проверка работы

1. Откройте вашего бота в Telegram
2. Отправьте \`/start\` - должно прийти приветственное сообщение
3. Попробуйте \`/register\` - проверьте флоу регистрации
4. От имени админа отправьте \`/pending\` - должен показать заявки

## Шаг 10: Остановка бота после тестирования

**Важно**: После завершения тестирования рекомендуется остановить бот, так как он еще не защищен от атак:

1. В Railway Dashboard → сервис бота → Settings
2. Нажмите **Pause Service**
3. Бот перестанет работать, но все данные сохранятся

## Следующие шаги

После успешного деплоя на Railway:
1. ✅ Протестировать все функции бота в production
2. Добавить капчу в флоу регистрации (безопасность)
3. Настроить алерты при падении бота (Railway → Settings → Notifications)
4. Настроить регулярные бэкапы PostgreSQL

## Troubleshooting

### Ошибка: "Bot failed to start"
- Проверьте логи деплоя
- Убедитесь, что BOT_TOKEN корректный
- Проверьте формат DATABASE_URL (должен быть \`postgresql+asyncpg://\`)

### Ошибка: "Database connection failed"
- Убедитесь, что PostgreSQL сервис запущен
- Проверьте DATABASE_URL (должен включать \`+asyncpg\`)
- Проверьте, что PostgreSQL в статусе "Active"

### Бот не отвечает на команды
- Проверьте логи: сообщение "Starting bot polling..." должно быть
- Убедитесь, что LEADER_TELEGRAM_ID указан правильно
- Проверьте статус сервиса в Railway Dashboard

### Миграции не применяются
- Проверьте логи: должно быть "Database tables created/verified"
- Убедитесь, что папка \`alembic/\` не исключена в .dockerignore
- Проверьте, что \`alembic.ini\` включен в Docker образ

## Полезные команды Railway CLI (опционально)

Установка CLI:
\`\`\`bash
npm i -g @railway/cli
railway login
\`\`\`

Просмотр логов:
\`\`\`bash
railway logs
\`\`\`

Просмотр переменных:
\`\`\`bash
railway variables
\`\`\`

## Дополнительная информация

Полная документация доступна в README.md
