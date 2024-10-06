import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from telegram.error import TelegramError

# --- НАСТРОЙКИ ---
TOKEN = '8058204517:AAGq6LwToiO6IR_oaTuw5P18YsBCn1lM4UU'
SOURCE_CHANNEL_ID = '-1002470156657'
TARGET_CHANNEL_ID = '-1002482136052'

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Функция для отображения инструкции с кнопками
async def forward_instructions(update: Update, context) -> None:
    logging.info(f"/start вызван пользователем {update.effective_user.id}")
    context.user_data['bot_paused'] = False  # Сбрасываем флаг при вызове /start

    keyboard = [
        [InlineKeyboardButton("Переслать 1", callback_data='1')],
        [InlineKeyboardButton("Переслать 3", callback_data='3')],
        [InlineKeyboardButton("Переслать 5", callback_data='5')],
        [InlineKeyboardButton("Переслать 10", callback_data='10')],
        [InlineKeyboardButton("Остановить бота", callback_data='stop')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = (
        "Для пересылки фотографий введите команду в формате:\n"
        "/forward [количество]\n\n"
        "Или выберите количество фотографий для пересылки, нажав на одну из кнопок ниже:\n"
        "Используйте кнопку для остановки бота."
    )

    await update.message.reply_text(message, reply_markup=reply_markup)
    logging.info("Отправлено стартовое сообщение с инструкциями и кнопками")

# Функция для обработки пересылки фотографий через кнопки
async def forward_photos_callback(update: Update, context) -> None:
    logging.info(f"Нажата кнопка пользователем {update.effective_user.id}, callback_data={update.callback_query.data}")
    
    if context.user_data.get('bot_paused', False):
        await update.callback_query.answer("Бот приостановлен. Используйте /start для его повторного запуска.")
        logging.warning("Попытка использования бота, когда он приостановлен")
        return
    
    query = update.callback_query
    await query.answer()  # Подтверждение выбора
    
    if query.data == 'stop':
        logging.info("Кнопка остановки бота нажата")
        await stop_bot(update, context)  # Вызов функции остановки бота
        return
    
    count = int(query.data)  # Количество фотографий из callback_data
    await update.effective_chat.send_message(f"Пересылаем последние {count} сообщения с фотографиями.")
    logging.info(f"Начата пересылка {count} сообщений")

# Функция для обработки новых сообщений из канала
async def handle_channel_post(update: Update, context) -> None:
    if context.user_data.get('bot_paused', False):
        logging.warning("Сообщение из канала игнорировано, т.к. бот приостановлен")
        return  # Прекращаем обработку, если бот остановлен

    message = update.channel_post
    logging.info(f"Получено новое сообщение из канала с ID: {message.message_id}")

    # Логирование всего сообщения, чтобы понять, что бот получает
    logging.info(f"Полученное сообщение: {message}")

    if message.photo:  # Проверяем, есть ли фотографии в сообщении
        logging.info(f"Сообщение содержит {len(message.photo)} фотографии(й)")
        for photo in message.photo:
            try:
                # Логируем информацию о попытке пересылки фотографии
                logging.info(f"Попытка пересылки фотографии с file_id: {photo.file_id}")
                
                # Пересылаем каждую фотографию в целевой канал
                await context.bot.send_photo(chat_id=TARGET_CHANNEL_ID, photo=photo.file_id)
                
                # Логируем успешную пересылку фотографии
                logging.info(f"Фотография {photo.file_id} успешно переслана")
            except TelegramError as e:
                logging.error(f"Ошибка при пересылке фотографии {photo.file_id}: {e}")
        
        try:
            # Удаление сообщения из канала
            await context.bot.delete_message(chat_id=SOURCE_CHANNEL_ID, message_id=message.message_id)
            logging.info(f"Сообщение {message.message_id} удалено из канала-источника")
        except TelegramError as e:
            logging.error(f"Ошибка при удалении сообщения {message.message_id}: {e}")
    else:
        logging.warning("Сообщение не содержит фотографий")

# Функция для остановки бота
async def stop_bot(update: Update, context) -> None:
    if update.callback_query:
        await update.callback_query.answer()  # Подтверждение остановки бота
        logging.info(f"Бот остановлен пользователем {update.effective_user.id}")
    
    context.user_data['bot_paused'] = True  # Устанавливаем флаг, что бот "приостановлен"
    await update.effective_chat.send_message("Бот приостановлен. Для повторного запуска используйте /start.")
    logging.info("Бот успешно приостановлен")

# Основная функция для запуска бота
def main():
    logging.info("Запуск бота")
    application = ApplicationBuilder().token(TOKEN).build()

    # Команда /start
    application.add_handler(CommandHandler('start', forward_instructions))

    # Обработка нажатий кнопок
    application.add_handler(CallbackQueryHandler(forward_photos_callback))

    # Обработка новых сообщений из канала
    application.add_handler(MessageHandler(filters.Chat(SOURCE_CHANNEL_ID) & filters.PHOTO, handle_channel_post))

    # Запуск бота
    application.run_polling()
    logging.info("Бот запущен и работает в режиме polling")

if __name__ == '__main__':
    main()