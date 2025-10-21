"""
Telegram bot that helps identify user and channel IDs.
Used for testing and demonstration purposes.
"""

import os
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.token import TokenValidationError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# /start command handler
@dp.message(F.text == '/start')
async def send_welcome(message: Message):
    user_id = message.from_user.id
    await message.reply(f"Your user ID: {user_id}")

# Forwarded message handler
@dp.message(F.forward_from_chat.type == 'channel')
async def handle_forwarded_message(message: Message):
    channel_id = message.forward_from_chat.id
    await message.reply(f"Channel ID: {channel_id}")

async def main():
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    except TokenValidationError:
        print("Invalid bot token. Please check your .env file.")

if __name__ == '__main__':
    asyncio.run(main())