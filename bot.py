import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from collections import deque
from dotenv import load_dotenv
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загружаем переменные из окружения
TOKEN = os.getenv('TOKEN')
ALLOWED_USER_ID = int(os.getenv('ALLOWED_USER_ID'))
SOURCE_CHANNEL_ID = int(os.getenv('SOURCE_CHANNEL_ID'))
TARGET_CHANNEL_ID = int(os.getenv('TARGET_CHANNEL_ID'))

# Очередь для хранения сообщений с изображениями (храним file_id, caption и message_id)
image_queue = deque()

# Функция для проверки, имеет ли пользователь доступ к боту
async def is_user_allowed(update: Update) -> bool:
    """Проверка доступа по user_id"""
    user_id = update.message.from_user.id if update.message else update.callback_query.from_user.id
    return user_id == ALLOWED_USER_ID

async def start(update: Update, context) -> None:
    """Отправляем меню с опциями при команде /start"""
    if not await is_user_allowed(update):
        await update.message.reply_text("У вас нет доступа к этому боту.")
        return

    keyboard = [
        [InlineKeyboardButton("Отправить 1", callback_data='1')],
        [InlineKeyboardButton("Отправить 3", callback_data='3')],
        [InlineKeyboardButton("Отправить 5", callback_data='5')],
        [InlineKeyboardButton("Отправить 10", callback_data='10')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    start_message = (
        "Привет! Я бот для обработки изображений между каналами.\n\n"
        "Вот список доступных команд:\n"
        "/start - Показать меню с выбором количества изображений для отправки.\n"
        "/send <количество> - Отправить указанное количество изображений из исходного канала в целевой. Если число не указано, отправляется одно изображение.\n"
        "Пример: /send 3 - отправляет 3 изображения.\n"
    )

    await update.message.reply_text(start_message, reply_markup=reply_markup)

async def button(update: Update, context) -> None:
    """Обработка нажатий кнопок"""
    if not await is_user_allowed(update):
        await update.callback_query.answer("У вас нет доступа к этому боту.", show_alert=True)
        return

    query = update.callback_query
    await query.answer()
    count = int(query.data)  # Количество изображений для отправки
    await send_images(context, count)

async def send_images(context, count: int) -> None:
    """Отправка изображений из очереди в целевой канал как новые сообщения"""
    if not image_queue:
        logger.info("Очередь изображений пуста.")
        return

    image_count = 0
    while image_queue and image_count < count:
        image_data = image_queue.popleft()  # Получаем данные старейшего изображения (file_id, caption и message_id)
        file_id = image_data['file_id']
        caption = image_data.get('caption', '')  # Обработка возможного отсутствия подписи
        message_id = image_data['message_id']

        try:
            # Лог перед удалением изображения
            logger.info(f"Попытка удалить изображение с ID {message_id} из исходного канала.")
            
            # Сначала пытаемся удалить изображение из исходного канала
            await context.bot.delete_message(chat_id=SOURCE_CHANNEL_ID, message_id=message_id)
            logger.info(f"Изображение с ID {message_id} успешно удалено из исходного канала.")
        except Exception as e:
            # Если изображение не удалось удалить (например, его уже нет), пропускаем его
            logger.warning(f"Ошибка при удалении изображения с ID {message_id}: {e}")
            continue  # Переходим к следующему изображению

        try:
            # Лог перед отправкой изображения
            logger.info(f"Попытка отправить изображение с ID {message_id} в целевой канал.")
            
            # Отправляем фото в целевой канал как новое сообщение
            await context.bot.send_photo(
                chat_id=TARGET_CHANNEL_ID,
                photo=file_id,  # Используем сохранённый file_id изображения
                caption=caption  # Подпись, если есть
            )
            image_count += 1
            logger.info(f"Изображение с ID {message_id} было успешно отправлено.")
        except Exception as e:
            logger.error(f"Ошибка при отправке изображения с ID {message_id}: {e}")

async def handle_new_image(update: Update, context) -> None:
    """Обработка новых сообщений с изображениями"""
    if update.channel_post and update.channel_post.chat_id == SOURCE_CHANNEL_ID and update.channel_post.photo:
        # Сохраняем file_id самого большого фото, caption (если есть) и message_id для удаления
        image_data = {
            'file_id': update.channel_post.photo[-1].file_id,  # Наибольшее разрешение фото
            'caption': update.channel_post.caption,  # Возможная подпись
            'message_id': update.channel_post.message_id  # ID сообщения для последующего удаления
        }
        image_queue.append(image_data)
        logger.info(f"Изображение с ID {update.channel_post.message_id} было добавлено в очередь.")

async def send_command(update: Update, context) -> None:
    """Обработка команды /send"""
    if not await is_user_allowed(update):
        await update.message.reply_text("У вас нет доступа к этому боту.")
        return

    try:
        count = int(context.args[0]) if context.args else 1  # Если указано число, используем его, иначе отправляем одно изображение
        await send_images(context, count)
    except ValueError:
        await update.message.reply_text("Пожалуйста, укажите правильное число.")
        logger.warning("Некорректный ввод числа при команде /send.")

def main():
    # Создаем приложение с вашим токеном
    app = ApplicationBuilder().token(TOKEN).build()

    # Добавляем обработчики
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("send", send_command))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.PHOTO & filters.Chat(SOURCE_CHANNEL_ID), handle_new_image))

    # Запускаем бота
    logger.info("Бот запущен.")
    app.run_polling(allowed_updates=Update.ALL_TYPES, read_timeout=10, write_timeout=10)

if __name__ == '__main__':
    main()