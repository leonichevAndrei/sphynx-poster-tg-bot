from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from collections import deque

# Ваш токен API от BotFather
TOKEN = '8058204517:AAGq6LwToiO6IR_oaTuw5P18YsBCn1lM4UU'

# ID канала, откуда бот будет обрабатывать изображения
SOURCE_CHANNEL_ID = -1002470156657
# ID канала, куда бот будет отправлять новые сообщения
TARGET_CHANNEL_ID = -1002482136052

# Очередь для хранения сообщений с изображениями (храним file_id, caption и message_id)
image_queue = deque()

async def start(update: Update, context) -> None:
    """Отправляем меню с опциями при команде /start"""
    keyboard = [
        [InlineKeyboardButton("Отправить 1", callback_data='1')],
        [InlineKeyboardButton("Отправить 3", callback_data='3')],
        [InlineKeyboardButton("Отправить 5", callback_data='5')],
        [InlineKeyboardButton("Отправить 10", callback_data='10')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Стартовое сообщение с описанием команд
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
    query = update.callback_query
    await query.answer()
    count = int(query.data)  # Количество изображений для отправки
    await send_images(context, count)

async def send_images(context, count: int) -> None:
    """Отправка изображений из очереди в целевой канал как новые сообщения"""
    image_count = 0
    while image_queue and image_count < count:
        image_data = image_queue.popleft()  # Получаем данные старейшего изображения (file_id, caption и message_id)
        file_id = image_data['file_id']
        caption = image_data.get('caption', '')  # Обработка возможного отсутствия подписи
        message_id = image_data['message_id']

        # Отправляем фото в целевой канал как новое сообщение
        await context.bot.send_photo(
            chat_id=TARGET_CHANNEL_ID,
            photo=file_id,  # Используем сохранённый file_id изображения
            caption=caption  # Подпись, если есть
        )

        # Удаляем сообщение из исходного канала
        await context.bot.delete_message(chat_id=SOURCE_CHANNEL_ID, message_id=message_id)

        image_count += 1

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

async def send_command(update: Update, context) -> None:
    """Обработка команды /send"""
    try:
        count = int(context.args[0]) if context.args else 1  # Если указано число, используем его, иначе отправляем одно изображение
        await send_images(context, count)
    except ValueError:
        await update.message.reply_text("Пожалуйста, укажите правильное число.")

def main():
    # Создаем приложение с вашим токеном
    app = ApplicationBuilder().token(TOKEN).build()

    # Добавляем обработчики
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("send", send_command))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.PHOTO & filters.Chat(SOURCE_CHANNEL_ID), handle_new_image))

    # Запускаем бота
    app.run_polling()

if __name__ == '__main__':
    main()