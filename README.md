# Kingdom Clash Clan Bot

Telegram бот для автоматизации управления кланом Kingdom Clash.

## Возможности (MVP)

- Регистрация новых игроков через /start (ник + скриншот профиля)
- Подтверждение регистрации главой клана через /accept
- Ручное добавление игроков через /add
- Хранение данных в Google Sheets

## Технологический стек

- Python 3.9+
- aiogram 3.3.0 - асинхронная библиотека для Telegram Bot API
- gspread - интеграция с Google Sheets API
- Docker - контейнеризация для деплоя

## Структура проекта

```
clan-bot/
├── config/           # Конфигурация и настройки
├── bot/              # Основной код бота
│   ├── handlers/     # Обработчики команд
│   ├── middlewares/  # Middleware (авторизация)
│   ├── keyboards/    # Клавиатуры (inline кнопки)
│   └── states/       # FSM состояния
├── database/         # Работа с данными (Google Sheets, temp storage)
├── models/           # Модели данных
├── utils/            # Вспомогательные функции
├── data/             # Временное хранилище (не в Git)
└── tests/            # Тесты

```

## Установка и запуск

### 1. Клонировать репозиторий

```bash
git clone https://github.com/YOUR_USERNAME/clan-bot.git
cd clan-bot
```

### 2. Создать виртуальное окружение

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows
```

### 3. Установить зависимости

```bash
pip install -r requirements.txt
```

### 4. Настроить окружение

Скопировать `.env.example` в `.env` и заполнить данные:

```bash
cp .env.example .env
nano .env
```

### 5. Настроить Google Sheets API

1. Создать проект в [Google Cloud Console](https://console.cloud.google.com/)
2. Включить Google Sheets API
3. Создать Service Account
4. Скачать `credentials.json` и поместить в `config/`
5. Создать Google Sheets таблицу
6. Дать доступ Service Account к таблице (по email из credentials.json)

### 6. Получить токен Telegram бота

1. Написать [@BotFather](https://t.me/BotFather)
2. Отправить `/newbot`
3. Следовать инструкциям
4. Скопировать токен в `.env`

### 7. Запустить бота

```bash
python bot/main.py
```

## Деплой на Railway.app

1. Зарегистрироваться на [Railway.app](https://railway.app)
2. Создать новый проект → Deploy from GitHub repo
3. Выбрать репозиторий `clan-bot`
4. Добавить переменные окружения из `.env`
5. Добавить Volume для папки `/app/data`
6. Деплой произойдет автоматически

## Структура Google Sheets

Таблица "Игроки":

| Telegram ID | Username | Nickname | Дата регистрации | Статус | Добавил | Примечания |
|-------------|----------|----------|------------------|--------|---------|------------|
| 123456789 | @player123 | DragonSlayer | 2026-01-12 | Активен | @clanleader | via /accept |

## Команды бота

Для пользователей:
- `/start` - Регистрация в клане (ник + скриншот)
- `/help` - Список команд
- `/cancel` - Отмена текущей операции

Для главы клана:
- `/accept @username` - Одобрить заявку на вступление
- `/add @username НикИгрока` - Добавить игрока вручную

## Разработка

### Запуск тестов

```bash
pytest tests/
```

### Docker (локально)

```bash
docker build -t clan-bot .
docker run --env-file .env -v $(pwd)/data:/app/data clan-bot
```

## Лицензия

MIT

## Контакты

Вопросы и предложения - создавайте Issues в репозитории.
