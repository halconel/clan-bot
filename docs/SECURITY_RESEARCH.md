# Исследование безопасности Telegram ботов

## Цель
Изучить лучшие практики безопасности для Telegram ботов и определить меры защиты для clan-bot.

## Ключевые угрозы

### 1. Flood атаки (спам)
- Множественные запросы регистрации от одного пользователя
- Массовая рассылка сообщений боту
- **Риск**: Перегрузка сервера, исчерпание квоты API Telegram

### 2. Автоматизированные боты
- Регистрация через автоматизированные скрипты
- Обход защиты без участия человека
- **Риск**: Заспамливание базы данных фейковыми заявками

### 3. SQL injection / XSS
- Вредоносный ввод в поля (ник, имя пользователя)
- **Риск**: Компрометация базы данных

### 4. Утечка токена бота
- Попадание BOT_TOKEN в публичный доступ
- **Риск**: Полный контроль над ботом злоумышленником

## Лучшие практики (из исследования)

### Rate Limiting
**Источник**: [Telegram Bot Security Best Practices](https://bazucompany.com/blog/how-to-secure-a-telegram-bot-best-practices/)

- Ограничение количества запросов на пользователя
- **Рекомендация**: Не более 10 сообщений в минуту от одного пользователя
- Telegram API сам имеет rate limits (status 429 - Too Many Requests)
- **Важно**: Уважать flood wait errors от Telegram

**Реализация**:
- Хранить timestamp последнего действия пользователя
- Проверять временной интервал перед обработкой команды
- Блокировать пользователя на N минут при превышении лимита

### Flood Protection
**Источник**: [Scaling Up: Flood Limits](https://grammy.dev/advanced/flood)

- **Определение flood**: > 10 сообщений в минуту
- Использовать request queue с throttling
- Exponential backoff при получении 429 ошибки
- Не игнорировать flood wait - это ведет к бану бота

### Captcha
**Источники**:
- [pyTelegramBotCAPTCHA](https://pypi.org/project/pyTelegramBotCAPTCHA/)
- [CaptchaBot на GitHub](https://github.com/Andrey-Ved/CaptchaBot)

**Типы капчи для Telegram ботов**:

1. **Текстовая капча**
   - Пользователь вводит текст с картинки
   - Сложность: Нужна генерация изображений
   - Плюсы: Эффективная защита от ботов
   - Минусы: Плохой UX, требует PIL/Pillow

2. **Математическая капча**
   - Простые примеры: "2 + 3 = ?"
   - Плюсы: Легко реализовать, понятно пользователю
   - Минусы: Легко обходится скриптами

3. **Кнопочная капча** ⭐ **Рекомендуется**
   - Inline кнопки с правильным/неправильным вариантом
   - Пример: "Нажмите на кнопку с числом 5" → [3] [5] [7]
   - Плюсы: Отличный UX, native Telegram UI, сложно автоматизировать
   - Минусы: Можно угадать (решается рандомизацией)

### Input Sanitization
- Валидировать длину ввода (у нас уже есть: 1-15 символов)
- Использовать prepared statements (SQLAlchemy ORM - защищает автоматически)
- Экранировать HTML (aiogram делает автоматически при ParseMode.HTML)

### Токен бота
- Хранить в переменных окружения ✅ (уже реализовано)
- Никогда не коммитить в Git ✅ (у нас в .gitignore)
- Регулярно ротировать токен (1 раз в 6-12 месяцев)

## Рекомендации для clan-bot

### Приоритет 1: Критично
1. ✅ **Защита токена** - уже реализовано
2. ✅ **Input validation** - уже реализовано (validators.py)
3. ⏳ **Капча при регистрации** - нужно добавить
4. ⏳ **Rate limiting** - нужно добавить

### Приоритет 2: Важно
5. ⏳ **Flood protection** - добавить middleware
6. ⏳ **Логирование подозрительной активности**
7. ⏳ **Уведомления админа о подозрительных действиях**

### Приоритет 3: Опционально
8. Monitoring и алерты (Railway Notifications)
9. Database backups (Railway PostgreSQL snapshots)
10. Регулярная ротация BOT_TOKEN

## Архитектурное решение

### 1. Капча (Кнопочная)
**Размещение**: После команды `/register`, перед вводом никнейма

**Флоу**:
```
/register
  → Правила клана
  → Капча: "Выберите правильный ответ: 2 + 3 = ?"
     [4] [5] [6]
  → (если правильно) → Введите ник
  → Загрузите скриншот
  → Заявка отправлена админу
```

**Реализация**:
- Новое состояние FSM: `waiting_for_captcha`
- Генерация случайного вопроса (пул из 2000+ вопросов из отдельного файла)
- 3 варианта ответа (1 правильный + 2 неправильных)
- Ограничение: 3 попытки, потом таймаут 5 минут

### 2. Rate Limiting
**Middleware** для всех хендлеров:
- Отслеживание действий пользователя в Redis/in-memory
- Лимит: 5 команд в минуту на пользователя
- При превышении: "⏱ Слишком много запросов. Повторите через X секунд"

### 3. Flood Protection
- Использовать встроенные механизмы aiogram
- Обработка 429 ошибок от Telegram API
- Exponential backoff при rate limit

## Источники

- [How to secure a Telegram bot: best practices](https://bazucompany.com/blog/how-to-secure-a-telegram-bot-best-practices/)
- [Scaling Up IV: Flood Limits | grammY](https://grammy.dev/advanced/flood)
- [Avoiding flood limits - python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot/wiki/Avoiding-flood-limits)
- [pyTelegramBotCAPTCHA](https://pypi.org/project/pyTelegramBotCAPTCHA/)
- [CaptchaBot GitHub](https://github.com/Andrey-Ved/CaptchaBot)
- [What are the Best Practices for Building Secure Telegram Bots?](https://alexhost.com/faq/what-are-the-best-practices-for-building-secure-telegram-bots/)

## Следующие шаги

1. ✅ Исследование завершено
2. ⏳ Реализовать кнопочную капчу
3. ⏳ Добавить rate limiting middleware
4. ⏳ Написать тесты
5. ⏳ Тестирование и деплой
