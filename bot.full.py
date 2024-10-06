from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from collections import deque

# Ваш токен API от BotFather
TOKEN = '8058204517:AAGq6LwToiO6IR_oaTuw5P18YsBCn1lM4UU'

# ID канала, откуда бот будет пересылать сообщения
SOURCE_CHANNEL_ID = -1002470156657
# ID канала, куда бот будет пересылать сообщения
TARGET_CHANNEL_ID = -1002482136052

# Очередь для хранения сообщений с изображениями
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
        "Привет! Я бот для пересылки изображений между каналами.\n\n"
        "Вот список доступных команд:\n"
        "/start - Показать меню с выбором количества изображений для пересылки.\n"
        "/forward <количество> - Переслать указанное количество изображений из исходного канала в целевой. Если число не указано, пересылается одно изображение.\n"
        "Пример: /forward 3 - пересылает 3 изображения.\n"
        "При успешной пересылке изображения будут удалены из исходного канала."
    )

    await update.message.reply_text(start_message, reply_markup=reply_markup)

async def button(update: Update, context) -> None:
    """Обработка нажатий кнопок"""
    query = update.callback_query
    await query.answer()
    count = int(query.data)
    await forward_images(context, count)

async def forward_images(context, count: int) -> None:
    """Пересылка изображений из очереди в целевой канал"""
    image_count = 0
    while image_queue and image_count < count:
        message_id = image_queue.popleft()  # Получаем ID старейшего сообщения
        await context.bot.forward_message(chat_id=TARGET_CHANNEL_ID, from_chat_id=SOURCE_CHANNEL_ID, message_id=message_id)
        await context.bot.delete_message(chat_id=SOURCE_CHANNEL_ID, message_id=message_id)  # Удаляем сообщение после пересылки
        image_count += 1

async def handle_new_image(update: Update, context) -> None:
    """Обработка новых сообщений с изображениями"""
    if update.channel_post and update.channel_post.chat_id == SOURCE_CHANNEL_ID and update.channel_post.photo:
        # Сохраняем ID сообщений с фото в очередь
        image_queue.append(update.channel_post.message_id)

async def forward_command(update: Update, context) -> None:
    """Обработка команды /forward"""
    try:
        count = int(context.args[0]) if context.args else 1  # Если указано число, используем его, иначе пересылаем одно изображение
        await forward_images(context, count)
    except ValueError:
        await update.message.reply_text("Пожалуйста, укажите правильное число.")

def main():
    # Создаем приложение с вашим токеном
    app = ApplicationBuilder().token(TOKEN).build()

    # Добавляем обработчики
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("forward", forward_command))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.PHOTO & filters.Chat(SOURCE_CHANNEL_ID), handle_new_image))

    # Запускаем бота
    app.run_polling()

if __name__ == '__main__':
    main()