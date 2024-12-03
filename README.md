# Telegram Avatar Bot 🤖

Telegram бот для создания стильных аватаров с применением шаблонов наложения.

## Возможности ✨

- Загрузка фотографий через Telegram
- Автоматическое обрезание фото в формат 1:1
- Наложение стильных шаблонов
- Пошаговый процесс создания
- Поддержка форматов JPG и PNG

## Команды бота 📝

- `/start` - Начало работы с ботом
- `/create` - Создание нового аватара
- `/info` - Информация о боте
- `/help` - Справка по использованию

## Установка 🛠

1. Клонируйте репозиторий:
```bash
git clone https://github.com/your-username/telegram-avatar-bot.git
cd telegram-avatar-bot
```

2. Создайте виртуальное окружение и активируйте его:
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Создайте файл .env и добавьте токен вашего бота:
```bash
cp .env.example .env
# Отредактируйте .env и добавьте ваш токен
```

## Запуск бота 🚀

```bash
python bot.py
```

## Процесс создания аватара 🎨

1. Отправьте команду `/create`
2. Загрузите фотографию
3. Подтвердите обрезанную версию
4. Выберите шаблон для наложения
5. Получите готовый аватар!

## Требования к фото 📸

- Формат: JPG или PNG
- Рекомендуемый размер: не менее 500x500 пикселей
- Фото будет автоматически обрезано до квадратного формата

## Разработка 💻

Для добавления новых шаблонов:
1. Добавьте PNG файл шаблона в корневую директорию
2. Обновите словарь `TEMPLATES` в файле `bot.py`

## Лицензия 📄

MIT License. См. файл [LICENSE](LICENSE) для подробностей.
