import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from PIL import Image
import cv2
import numpy as np
import io

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Доступные шаблоны
TEMPLATES = {
    'template1': 'lay_01.png',
    'template2': 'lay_02.png',
}

# Допустимые форматы изображений
ALLOWED_FORMATS = {'image/jpeg', 'image/png', 'image/jpg'}

# Состояния создания аватара
STATES = {
    'WAITING_PHOTO': 1,
    'WAITING_TEMPLATE': 2
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправляет сообщение при команде /start."""
    welcome_message = (
        "👋 Добро пожаловать в Аватарный бот!\n\n"
        "Отправьте мне фотографию, и я помогу добавить на неё красивые наложения.\n"
        "Доступные команды:\n"
        "/create - Создать новый аватар\n"
        "/info - Информация о боте\n"
        "/help - Справка по использованию"
    )
    # Сбрасываем состояние при старте
    context.user_data.clear()
    await update.message.reply_text(welcome_message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправляет сообщение при команде /help."""
    help_text = (
        "🔍 Как пользоваться ботом:\n\n"
        "1. Используйте команду /create для создания аватара\n"
        "2. Отправьте любое фото, которое хотите улучшить\n"
        "3. Выберите шаблон из доступных вариантов\n"
        "4. Дождитесь обработанного фото\n\n"
        "Команды:\n"
        "/create - Создать новый аватар\n"
        "/info - Информация о боте\n"
        "/help - Показать это справочное сообщение"
    )
    await update.message.reply_text(help_text)

async def create_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка команды /create."""
    create_message = (
        "🎨 Давайте создадим ваш новый аватар!\n\n"
        "📝 Требования к фото:\n"
        "• Формат: JPG или PNG\n"
        "• Рекомендуемый размер: не менее 500x500 пикселей\n"
        "• Фото будет автоматически обрезано до квадратного формата\n\n"
        "✨ Процесс создания:\n"
        "1️⃣ Загрузите фото (можно отправить как фото или как файл)\n"
        "2️⃣ Просмотрите и подтвердите обрезанную версию\n"
        "3️⃣ Выберите шаблон для наложения\n\n"
        "Отправьте ваше фото! 📸"
    )
    # Устанавливаем состояние ожидания фото
    context.user_data['state'] = STATES['WAITING_PHOTO']
    await update.message.reply_text(create_message)

async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка команды /info."""
    info_message = (
        "ℹ️ О боте:\n\n"
        "🤖 Бот Фото Наложений - ваш персональный помощник в создании стильных аватаров!\n\n"
        "Возможности:\n"
        "✨ Создание уникальных аватаров\n"
        "🎭 Различные шаблоны наложений\n"
        "🖼 Поддержка различных форматов изображений\n"
        "⚡️ Быстрая обработка фото\n\n"
        "Версия: 1.0\n"
        "Разработчик: @nplxdesign\n\n"
        "Для начала работы используйте команду /create"
    )
    await update.message.reply_text(info_message)

def create_template_keyboard():
    """Создает встроенную клавиатуру с вариантами шаблонов."""
    keyboard = [
        [InlineKeyboardButton(f"Шаблон {i+1}", callback_data=f"template{i+1}")]
        for i in range(len(TEMPLATES))
    ]
    return InlineKeyboardMarkup(keyboard)

async def crop_to_square(photo_bytes: bytes) -> bytes:
    """Обрезает фото до квадратного формата."""
    # Конвертируем bytes в numpy array
    nparr = np.frombuffer(photo_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is None:
        raise ValueError("Не удалось открыть изображение")
    
    height, width = img.shape[:2]
    
    # Определяем размер квадрата
    size = min(height, width)
    
    # Вычисляем координаты для обрезки
    start_x = (width - size) // 2
    start_y = (height - size) // 2
    
    # Обрезаем изображение
    cropped = img[start_y:start_y+size, start_x:start_x+size]
    
    # Конвертируем обратно в bytes
    is_success, buffer = cv2.imencode(".png", cropped)
    if not is_success:
        raise ValueError("Не удалось сохранить обработанное изображение")
    
    return buffer.tobytes()

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка полученных фотографий."""
    # Проверяем, что пользователь находится в процессе создания аватара
    if context.user_data.get('state') != STATES['WAITING_PHOTO']:
        await update.message.reply_text(
            "Чтобы создать новый аватар, используйте команду /create"
        )
        return

    try:
        # Определяем, как было отправлено изображение
        if update.message.document:
            # Если отправлено как файл, проверяем формат
            if update.message.document.mime_type not in ALLOWED_FORMATS:
                await update.message.reply_text(
                    "❌ Неподдерживаемый формат файла!\n"
                    "Пожалуйста, отправьте изображение в формате JPG или PNG, "
                    "или отправьте фото через стандартный механизм Telegram."
                )
                return
            # Получаем файл из документа
            photo_file = await update.message.document.get_file()
        elif update.message.photo:
            # Если отправлено как фото, берём максимальный размер
            photo = update.message.photo[-1]
            photo_file = await photo.get_file()
        else:
            await update.message.reply_text(
                "❌ Пожалуйста, отправьте фотографию."
            )
            return
        
        await update.message.reply_text("⏳ Обрабатываем ваше фото...")
        
        try:
            # Скачиваем фото
            photo_bytes = await photo_file.download_as_bytearray()
            
            # Обрезаем фото до квадрата
            cropped_bytes = await crop_to_square(photo_bytes)
            
            # Сохраняем обработанное фото в контексте
            context.user_data['photo_bytes'] = cropped_bytes
            
            # Создаем клавиатуру для подтверждения
            keyboard = [
                [
                    InlineKeyboardButton("✅ Использовать это фото", callback_data="accept_crop"),
                    InlineKeyboardButton("🔄 Загрузить другое", callback_data="reject_crop")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Отправляем превью обрезанного фото
            await update.message.reply_photo(
                photo=cropped_bytes,
                caption="🖼 Вот ваше фото в формате 1:1\n"
                        "Хотите использовать его или загрузить другое?",
                reply_markup=reply_markup
            )
            
            # Обновляем состояние
            context.user_data['state'] = STATES['WAITING_TEMPLATE']
            
        except Exception as e:
            logger.error(f"Ошибка при обработке изображения: {e}")
            await update.message.reply_text(
                "❌ Произошла ошибка при обработке изображения.\n"
                "Пожалуйста, попробуйте другое фото."
            )
            
    except Exception as e:
        logger.error(f"Ошибка при получении файла: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка при получении файла.\n"
            "Пожалуйста, попробуйте отправить фото еще раз."
        )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка всех callback запросов."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "accept_crop":
        # Показываем шаблоны для выбора
        await query.edit_message_caption(
            caption="🎭 Отлично! Теперь выберите шаблон для наложения:",
            reply_markup=create_template_keyboard()
        )
    elif query.data == "reject_crop":
        # Просим загрузить новое фото
        context.user_data['state'] = STATES['WAITING_PHOTO']
        await query.edit_message_caption(
            caption="📸 Хорошо, загрузите другое фото!"
        )
    elif query.data.startswith("template"):
        await handle_template_selection(update, context)

async def handle_template_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора шаблона."""
    query = update.callback_query
    
    template_name = query.data
    if template_name not in TEMPLATES:
        await query.edit_message_caption(
            caption="❌ Неверный выбор шаблона. Пожалуйста, попробуйте снова."
        )
        return
    
    # Получаем сохраненное фото
    photo_bytes = context.user_data.get('photo_bytes')
    if not photo_bytes:
        await query.edit_message_caption(
            caption="❌ Фото не найдено. Пожалуйста, начните сначала с команды /create"
        )
        return
    
    await query.edit_message_caption(
        caption="⏳ Накладываем выбранный шаблон... Пожалуйста, подождите!"
    )
    
    # Применяем шаблон
    template_path = TEMPLATES[template_name]
    try:
        result_bytes = await apply_template(photo_bytes, template_path)
        
        # Отправляем обработанное фото
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=result_bytes,
            caption="✨ Ваш новый аватар готов! 🎨\n\n"
                    "Чтобы создать новый, используйте команду /create"
        )
        
        # Очищаем данные пользователя
        context.user_data.clear()
        
    except Exception as e:
        logger.error(f"Ошибка обработки фото: {e}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="❌ Извините, произошла ошибка при обработке вашего фото.\n"
                 "Пожалуйста, попробуйте снова с команды /create"
        )

async def apply_template(photo_bytes: bytes, template_path: str) -> bytes:
    """Применяет шаблон наложения к фото."""
    # Открываем фото пользователя
    with Image.open(io.BytesIO(photo_bytes)) as user_photo:
        # Преобразуем в RGBA если необходимо
        if user_photo.mode != 'RGBA':
            user_photo = user_photo.convert('RGBA')
        
        # Открываем и изменяем размер шаблона для совпадения с размером фото
        with Image.open(template_path) as template:
            template = template.convert('RGBA')
            template = template.resize(user_photo.size, Image.Resampling.LANCZOS)
            
            # Компонуем изображения
            result = Image.alpha_composite(user_photo, template)
            
            # Сохраняем результат в байты
            output = io.BytesIO()
            result.save(output, format='PNG')
            output.seek(0)
            return output.getvalue()

def main():
    """Запуск бота."""
    # Создаем приложение
    application = Application.builder().token(os.getenv('TELEGRAM_BOT_TOKEN')).build()

    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("create", create_command))
    application.add_handler(CommandHandler("info", info_command))
    application.add_handler(MessageHandler(filters.PHOTO | filters.Document.IMAGE, handle_photo))
    application.add_handler(CallbackQueryHandler(handle_callback))

    # Запускаем бота
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
