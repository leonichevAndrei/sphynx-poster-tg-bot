from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters

# Ваш токен API от BotFather
TOKEN = '8058204517:AAGq6LwToiO6IR_oaTuw5P18YsBCn1lM4UU'

# ID канала, откуда бот будет пересылать сообщения
SOURCE_CHANNEL_ID = -1002470156657  # ID исходного канала
# ID канала, куда бот будет пересылать сообщения
TARGET_CHANNEL_ID = -1002482136052  # ID целевого канала

async def forward_message(update: Update, context) -> None:
    # Проверяем, что сообщение пришло из исходного канала
    if update.channel_post and update.channel_post.chat_id == SOURCE_CHANNEL_ID:
        # Пересылаем сообщение в целевой канал
        await context.bot.forward_message(
            chat_id=TARGET_CHANNEL_ID, 
            from_chat_id=update.channel_post.chat_id, 
            message_id=update.channel_post.message_id
        )

def main():
    # Создаем приложение с вашим токеном
    app = ApplicationBuilder().token(TOKEN).build()

    # Добавляем обработчик для пересылки сообщений из исходного канала
    app.add_handler(MessageHandler(filters.Chat(SOURCE_CHANNEL_ID), forward_message))

    # Запускаем бота
    app.run_polling()

if __name__ == '__main__':
    main()