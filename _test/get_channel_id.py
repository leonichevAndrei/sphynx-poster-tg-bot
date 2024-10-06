import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

# --- НАСТРОЙКИ ---
TOKEN = '8058204517:AAGq6LwToiO6IR_oaTuw5P18YsBCn1lM4UU'

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Функция для обработки команды /start
async def start(update: Update, context) -> None:
    await update.message.reply_text("Отправьте сообщение в канал, чтобы увидеть его ID.")
    logging.info(f"Команда /start вызвана пользователем {update.effective_user.id}")

# Функция для вывода информации об обновлениях
async def handle_updates(update: Update, context) -> None:
    logging.info(f"Обновление: {update}")
    if update.channel_post:
        logging.info(f"Сообщение из канала с ID: {update.channel_post.chat.id}")

def main():
    # Создание приложения Telegram Bot
    application = ApplicationBuilder().token(TOKEN).build()

    # Обработка команды /start
    application.add_handler(CommandHandler('start', start))

    # Обработка всех обновлений
    application.add_handler(MessageHandler(filters.ALL, handle_updates))

    # Запуск бота
    logging.info("Бот запущен для получения ID канала")
    application.run_polling()

if __name__ == '__main__':
    main()