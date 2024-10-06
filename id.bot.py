import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.token import TokenValidationError
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

API_TOKEN = os.getenv('BOT_TOKEN')

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Обработчик команды /start
@dp.message(F.text == '/start')
async def send_welcome(message: Message):
    user_id = message.from_user.id
    await message.reply(f"Ваш ID: {user_id}")

# Обработчик пересланного сообщения
@dp.message(F.forward_from_chat.type == 'channel')
async def handle_forwarded_message(message: Message):
    channel_id = message.forward_from_chat.id
    await message.reply(f"ID канала: {channel_id}")

async def main():
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    except TokenValidationError:
        print("Ошибка с токеном. Проверьте его корректность.")

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())