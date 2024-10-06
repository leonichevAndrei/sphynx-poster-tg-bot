from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters

TOKEN = '8058204517:AAGq6LwToiO6IR_oaTuw5P18YsBCn1lM4UU'
TARGET_CHANNEL_ID = '-1002470156657'

# Функция для обработки сообщений с фотографиями
async def handle_photo(update: Update, context) -> None:
    message = update.channel_post
    if message.photo:
        for photo in message.photo:
            # Пересылаем фотографию в целевой канал
            await context.bot.send_photo(chat_id=TARGET_CHANNEL_ID, photo=photo.file_id)
            print(f"Переслана фотография с file_id: {photo.file_id}")

def main():
    application = ApplicationBuilder().token(TOKEN).build()

    # Обработка сообщений с фотографиями
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    # Запуск бота
    application.run_polling()

if __name__ == '__main__':
    main()