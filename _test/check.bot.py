import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

# --- НАСТРОЙКИ ---
TOKEN = '8058204517:AAGq6LwToiO6IR_oaTuw5P18YsBCn1lM4UU'
SOURCE_CHANNEL_ID = '-1002470156657'  # Канал-источник

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Функция для обработки команды /start
async def start(update: Update, context) -> None:
    await update.message.reply_text("Бот запущен. Проверка сообщений канала началась.")
    logging.info(f"Команда /start вызвана пользователем {update.effective_user.id}")

# Функция для проверки сообщений в канале
async def check_channel_messages(update: Update, context) -> None:
    message = update.channel_post
    if message:
        logging.info(f"Получено сообщение из канала: {message.text or 'Сообщение не содержит текста'}")
    else:
        logging.info("Сообщение не распознано ботом")

def main():
    # Создание приложения Telegram Bot
    application = ApplicationBuilder().token(TOKEN).build()

    # Обработка команды /start
    application.add_handler(CommandHandler('start', start))

    # Обработка сообщений из канала-источника
    application.add_handler(MessageHandler(filters.Chat(SOURCE_CHANNEL_ID), check_channel_messages))

    # Запуск бота
    logging.info("Бот запущен для проверки сообщений в канале")
    application.run_polling()

if __name__ == '__main__':
    main()