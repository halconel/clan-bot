# Локальное тестирование бота

Руководство по запуску и тестированию бота на локальной машине с использованием Docker Compose.

## Предварительные требования

1. **Docker и Docker Compose** установлены на вашей системе
2. **UV** - менеджер пакетов Python (уже установлен)
3. **Git** для управления кодом

## Шаг 1: Получение Telegram Bot Token

### 1.1. Создание бота через BotFather

1. Откройте Telegram и найдите [@BotFather](https://t.me/BotFather)
2. Отправьте команду `/newbot`
3. Укажите имя бота (например: "Clan Registration Bot Test")
4. Укажите username бота (должен заканчиваться на `bot`, например: `test_clan_reg_bot`)
5. Скопируйте токен, который BotFather отправит вам

**Формат токена:** `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`

### 1.2. Получение вашего Telegram ID

1. Откройте [@userinfobot](https://t.me/userinfobot) в Telegram
2. Отправьте любое сообщение
3. Бот ответит вашим Telegram ID (например: `123456789`)

## Шаг 2: Создание .env файла

Создайте файл `.env` в корне проекта:

```bash
cd /home/dmitriy/workspace/pet-projects/clan-bot
cp .env.example .env
```

Отредактируйте `.env` файл и укажите ваши данные:

```env
# Telegram Bot Configuration
BOT_TOKEN=YOUR_BOT_TOKEN_FROM_BOTFATHER
LEADER_TELEGRAM_ID=YOUR_TELEGRAM_ID

# Database Configuration (для docker-compose)
DATABASE_URL=postgresql+asyncpg://clan_bot_user:clan_bot_password@localhost:5432/clan_bot

# Storage Configuration
SCREENSHOTS_DIR=data/screenshots
TEMP_STORAGE_FILE=data/pending.json

# Logging
LOG_LEVEL=DEBUG
LOG_FILE=bot.log
```

**Важно:** Замените:
- `YOUR_BOT_TOKEN_FROM_BOTFATHER` на токен из BotFather
- `YOUR_TELEGRAM_ID` на ваш Telegram ID

## Шаг 3: Запуск PostgreSQL через Docker Compose

### 3.1. Запустить PostgreSQL в фоновом режиме

```bash
docker-compose up -d postgres
```

### 3.2. Проверить что PostgreSQL запущен

```bash
docker-compose ps
```

Вывод должен показать:
```
NAME                    IMAGE                  STATUS
clan-bot-postgres       postgres:15-alpine     Up X seconds
```

### 3.3. Проверить логи PostgreSQL (опционально)

```bash
docker-compose logs postgres
```

## Шаг 4: Применение миграций Alembic

Примените миграции базы данных:

```bash
PATH="$HOME/snap/code/218/.local/share/../bin:$PATH" uv run alembic upgrade head
```

Вывод должен содержать:
```
INFO  [alembic.runtime.migration] Running upgrade  -> 76c8ee5e74c9, initial tables
INFO  [alembic.runtime.migration] Running upgrade 76c8ee5e74c9 -> 617d74853330, add exclusion fields to players table
```

## Шаг 5: Создание директорий для данных

Создайте директории для скриншотов:

```bash
mkdir -p data/screenshots
```

## Шаг 6: Запуск бота

Запустите бота локально:

```bash
PATH="$HOME/snap/code/218/.local/share/../bin:$PATH" uv run python main.py
```

Вывод должен содержать:
```
INFO:database.database:Database engine initialized successfully
INFO:database.database:Session factory initialized successfully
INFO:database.database:Database tables created successfully
INFO:__main__:Starting bot polling...
```

## Шаг 7: Тестирование бота

### 7.1. Откройте вашего бота в Telegram

Найдите бота по username, который вы создали (например: `@test_clan_reg_bot`)

### 7.2. Тестовые сценарии

#### Сценарий 1: Регистрация нового игрока

1. Отправьте `/start` - бот должен ответить приветствием
2. Отправьте `/help` - бот покажет список команд
3. Отправьте `/register` - начнется процесс регистрации
4. Введите игровой никнейм (например: `TestPlayer`)
5. Отправьте любое фото (скриншот профиля)
6. Бот отправит уведомление вам (как админу) с кнопками "Одобрить" / "Отклонить"

#### Сценарий 2: Одобрение заявки (как админ)

1. Нажмите кнопку "✅ Одобрить" в уведомлении
2. Бот отправит подтверждение игроку
3. Проверьте `/list` - игрок должен появиться в списке активных

#### Сценарий 3: Просмотр заявок

1. Отправьте `/pending` - увидите список ожидающих заявок (если есть)

#### Сценарий 4: Просмотр всех игроков

1. Отправьте `/list` - увидите список всех зарегистрированных игроков

#### Сценарий 5: Отчисление игрока

1. Отправьте `/exclude @testplayer Причина отчисления`
2. Бот отчислит игрока и отправит ему уведомление
3. Проверьте `/list` - игрок должен быть в списке отчисленных

#### Сценарий 6: Отмена регистрации

1. Начните регистрацию: `/register`
2. Отправьте `/cancel` - регистрация будет отменена

### 7.3. Проверка базы данных

Подключитесь к PostgreSQL через psql:

```bash
docker exec -it clan-bot-postgres psql -U clan_bot_user -d clan_bot
```

Выполните SQL запросы:

```sql
-- Посмотреть всех игроков
SELECT * FROM players;

-- Посмотреть ожидающие заявки
SELECT * FROM pending_registrations;

-- Выйти
\q
```

## Шаг 8: Остановка бота и очистка

### 8.1. Остановить бота

Нажмите `Ctrl+C` в терминале, где запущен бот.

### 8.2. Остановить PostgreSQL

```bash
docker-compose down
```

### 8.3. Удалить данные (опционально)

Если хотите начать с чистой базы:

```bash
docker-compose down -v  # Удалит Docker volumes с данными PostgreSQL
rm -rf data/screenshots/*  # Удалит скриншоты
```

## Troubleshooting

### Проблема: "command not found: uv"

**Решение:**
```bash
# Добавьте UV в PATH перед командами
export PATH="$HOME/snap/code/218/.local/share/../bin:$PATH"

# Или добавьте в ~/.zshrc (уже должно быть)
echo 'export PATH="$HOME/snap/code/218/.local/share/../bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### Проблема: "Database connection failed"

**Решение:**
```bash
# Проверьте что PostgreSQL запущен
docker-compose ps

# Проверьте логи
docker-compose logs postgres

# Перезапустите PostgreSQL
docker-compose restart postgres
```

### Проблема: "Bot token is invalid"

**Решение:**
- Проверьте правильность токена в `.env`
- Убедитесь, что токен не содержит пробелов
- Создайте нового бота через @BotFather

### Проблема: "Permission denied" для data/screenshots

**Решение:**
```bash
chmod -R 755 data/
```

### Проблема: Бот не отвечает на команды

**Решение:**
1. Убедитесь, что бот запущен (`uv run python main.py`)
2. Проверьте логи в терминале на ошибки
3. Убедитесь, что вы используете правильный username бота
4. Проверьте, что BOT_TOKEN правильный

### Проблема: Миграции не применяются

**Решение:**
```bash
# Проверьте текущую версию миграций
PATH="$HOME/snap/code/218/.local/share/../bin:$PATH" uv run alembic current

# Проверьте историю миграций
PATH="$HOME/snap/code/218/.local/share/../bin:$PATH" uv run alembic history

# Откатите и примените заново
PATH="$HOME/snap/code/218/.local/share/../bin:$PATH" uv run alembic downgrade base
PATH="$HOME/snap/code/218/.local/share/../bin:$PATH" uv run alembic upgrade head
```

## Полезные команды

### Docker Compose

```bash
# Запустить все сервисы
docker-compose up

# Запустить в фоне
docker-compose up -d

# Остановить
docker-compose down

# Посмотреть логи
docker-compose logs -f

# Перезапустить сервис
docker-compose restart postgres
```

### База данных

```bash
# Подключиться к PostgreSQL
docker exec -it clan-bot-postgres psql -U clan_bot_user -d clan_bot

# Экспорт данных
docker exec -it clan-bot-postgres pg_dump -U clan_bot_user clan_bot > backup.sql

# Импорт данных
cat backup.sql | docker exec -i clan-bot-postgres psql -U clan_bot_user -d clan_bot
```

### Alembic

```bash
# Текущая версия
uv run alembic current

# История миграций
uv run alembic history

# Создать новую миграцию
uv run alembic revision --autogenerate -m "Description"

# Применить миграции
uv run alembic upgrade head

# Откатить последнюю миграцию
uv run alembic downgrade -1
```

## Следующие шаги

После успешного локального тестирования вы можете:

1. **Деплой на Railway.app** - см. [docs/RAILWAY_SETUP.md](RAILWAY_SETUP.md)
2. **Написать больше тестов** - см. [tests/](../tests/)
3. **Добавить новые фичи** - см. Implementation Plan в [.claude/plans/](../.claude/plans/)

## Дополнительная информация

- [README.md](../README.md) - Основная документация
- [RAILWAY_SETUP.md](RAILWAY_SETUP.md) - Деплой на Railway
- [Implementation Plan](.claude/plans/) - План разработки
