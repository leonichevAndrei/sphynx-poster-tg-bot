"""
Telegram bot that relays photos from a source channel to a target channel.
Features:
- Collects incoming photos from a source channel into a FIFO queue
- Sends N photos on demand (/send) or on a daily schedule (job queue)
- Deletes the original message in the source channel after enqueueing, then posts as a new message in the target channel
"""

import os
import logging
from collections import deque
from datetime import time

import pytz
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# Load environment variables
load_dotenv()

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables (align with .env.example)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ALLOWED_USER_ID = int(os.getenv("ALLOWED_USER_ID", "0"))          # user ID allowed to interact with commands
SOURCE_CHANNEL_ID = int(os.getenv("SOURCE_CHANNEL_ID", "0"))      # channel ID to listen for new photos
TARGET_CHANNEL_ID = int(os.getenv("TARGET_CHANNEL_ID", "0"))      # channel ID to post photos to

# Daily schedule settings
POSTS_PER_DAY = int(os.getenv("POSTS_PER_DAY", "10"))             # default: 10 images per day
TIMEZONE = os.getenv("TIMEZONE", "Europe/Moscow")                 # default timezone
SEND_HOUR = int(os.getenv("DAILY_SEND_HOUR", "10"))               # default: 10:00
SEND_MINUTE = int(os.getenv("DAILY_SEND_MINUTE", "0"))            # default: 10:00

# Timezone object
tz = pytz.timezone(TIMEZONE)

# FIFO queue to store incoming images: file_id, caption, message_id
image_queue: deque[dict] = deque()


async def is_user_allowed(update: Update) -> bool:
    """Check if the user is allowed to use the bot (by user_id)."""
    user_id = (
        update.effective_user.id
        if update.effective_user
        else 0
    )
    return ALLOWED_USER_ID == 0 or user_id == ALLOWED_USER_ID


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a small menu with quick actions on /start."""
    if not await is_user_allowed(update):
        if update.effective_message:
            await update.effective_message.reply_text("You are not allowed to use this bot.")
        return

    keyboard = [
        [InlineKeyboardButton("Send 1", callback_data="1")],
        [InlineKeyboardButton("Send 3", callback_data="3")],
        [InlineKeyboardButton("Send 5", callback_data="5")],
        [InlineKeyboardButton("Send 10", callback_data="10")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = (
        "Hi! This bot relays images from a source channel to a target channel.\n\n"
        f"Daily it sends {POSTS_PER_DAY} images at {SEND_HOUR:02}:{SEND_MINUTE:02} ({TIMEZONE}).\n\n"
        "Commands:\n"
        "/start — show menu\n"
        "/send <n> — send <n> images from queue (default: 1)\n"
        "Example: /send 3\n"
    )
    await update.effective_message.reply_text(text, reply_markup=reply_markup)


async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline keyboard button clicks."""
    if not await is_user_allowed(update):
        if update.callback_query:
            await update.callback_query.answer("Not allowed.", show_alert=True)
        return

    query = update.callback_query
    await query.answer()
    count = int(query.data)
    await send_images(context, count)


async def send_images(context: ContextTypes.DEFAULT_TYPE, count: int) -> None:
    """Send up to <count> images from queue to target channel, deleting originals in source channel."""
    if not image_queue:
        logger.info("Image queue is empty.")
        return

    sent = 0
    while image_queue and sent < count:
        image_data = image_queue.popleft()
        file_id = image_data["file_id"]
        caption = image_data.get("caption") or ""
        message_id = image_data["message_id"]

        # Try to delete original message in source channel
        try:
            logger.info("Deleting original message %s from source channel %s", message_id, SOURCE_CHANNEL_ID)
            await context.bot.delete_message(chat_id=SOURCE_CHANNEL_ID, message_id=message_id)
        except Exception as e:
            logger.warning("Failed to delete source message %s: %s", message_id, e)
            # Continue anyway (still try to send to target)

        # Send as a new photo to the target channel
        try:
            logger.info("Sending image %s to target channel %s", message_id, TARGET_CHANNEL_ID)
            await context.bot.send_photo(chat_id=TARGET_CHANNEL_ID, photo=file_id, caption=caption)
            sent += 1
        except Exception as e:
            logger.error("Failed to send image %s: %s", message_id, e)


async def handle_new_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle new photos in the source channel: enqueue file_id, caption, message_id."""
    channel_post = update.channel_post
    if not channel_post:
        return

    if channel_post.chat_id == SOURCE_CHANNEL_ID and channel_post.photo:
        image_queue.append(
            {
                "file_id": channel_post.photo[-1].file_id,  # largest size
                "caption": channel_post.caption,
                "message_id": channel_post.message_id,
            }
        )
        logger.info("Enqueued image from message %s", channel_post.message_id)


async def send_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /send <n>."""
    if not await is_user_allowed(update):
        await update.effective_message.reply_text("You are not allowed to use this bot.")
        return

    try:
        n = int(context.args[0]) if context.args else 1
        await send_images(context, n)
    except ValueError:
        await update.effective_message.reply_text("Please provide a valid number (e.g., /send 3).")
        logger.warning("Invalid number in /send command.")


async def scheduled_send_images(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Job: send N images daily at the configured time."""
    logger.info("Scheduled job started: sending %s images", POSTS_PER_DAY)
    await send_images(context, POSTS_PER_DAY)


def main() -> None:
    # Build application
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("send", send_command))
    app.add_handler(CallbackQueryHandler(on_button))

    # Listen to photos posted in the source channel
    app.add_handler(MessageHandler(filters.PHOTO & filters.Chat(SOURCE_CHANNEL_ID), handle_new_image))

    # Daily job
    app.job_queue.run_daily(
        scheduled_send_images,
        time(timezone=tz, hour=SEND_HOUR, minute=SEND_MINUTE),
    )

    logger.info("Bot started (polling).")
    app.run_polling(allowed_updates=Update.ALL_TYPES, read_timeout=10, write_timeout=10)


if __name__ == "__main__":
    main()