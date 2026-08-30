import asyncio
import os
import sys

from aiogram import Bot, Dispatcher
from aiogram.types import Message
from dotenv import load_dotenv


async def handle_incoming_message(message: Message) -> None:
    sender_name: str = (
        message.from_user.username
        if message.from_user and message.from_user.username
        else "Unknown"
    )
    sender_id: int = message.from_user.id if message.from_user else 0
    text: str = message.text or "<non-text content>"

    sys.stdout.write(
        f"\n[RECEIVED] From: @{sender_name} (ID: {sender_id})\nText: {text}\n\n"
    )
    sys.stdout.flush()

    await message.answer(f"Echo received: {text}")


async def run_listener() -> None:
    load_dotenv()
    token: str | None = os.getenv("TELEGRAM_BOT_TOKEN")

    if not token or token == "your_telegram_bot_token_here":
        sys.stderr.write("ERROR: TELEGRAM_BOT_TOKEN is not configured in .env\n")
        sys.exit(1)

    bot: Bot = Bot(token=token)
    dp: Dispatcher = Dispatcher()

    dp.message.register(handle_incoming_message)

    bot_user = await bot.get_me()
    sys.stdout.write(f"Listening for messages on @{bot_user.username}...\n")
    sys.stdout.write("Send any message in Telegram to verify live receipt.\n")
    sys.stdout.flush()

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


def main() -> None:
    asyncio.run(run_listener())


if __name__ == "__main__":
    main()
