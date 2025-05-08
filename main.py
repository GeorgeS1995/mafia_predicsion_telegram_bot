import asyncio
import datetime
import logging
import os
import random
import sys
from dataclasses import dataclass
from datetime import timedelta

from aiogram.types import BotCommand

from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.filters.command import Command
from aiogram.types import Message
from aiogram.types.input_file import FSInputFile
from pathlib import Path

ENV_PREFIX = "MAFIA_PREDICTION_BOT_"
# Bot token can be obtained via https://t.me/BotFather
TELEGRAM_TOKEN = os.getenv(f"{ENV_PREFIX}TELEGRAM_TOKEN")
PATH_TO_PREDICTION_MEMES = os.getenv(f"{ENV_PREFIX}PATH_TO_PREDICTION_MEMES", "./prediction_memes")
PREDICTION_DURATION_IN_SECONDS = int(os.getenv(f"{ENV_PREFIX}PREDICTION_DURATION_IN_SECONDS", 10))

# All handlers should be attached to the Router (or Dispatcher)
dp = Dispatcher()

@dataclass
class PredictionData:
    file_name: str
    expired_at: datetime.datetime

    @property
    def abs_file_path(self) -> Path:
        return Path(PATH_TO_PREDICTION_MEMES, self.file_name).resolve()

PREDICTION_FILES_IN_USE: set[str] = set()
IN_MEMORY_PREDICTION_DB: dict[int, PredictionData] = {}


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    This handler receives messages with `/start` command
    """
    # Most event objects have aliases for API methods that can be called in events' context
    # For example if you want to answer to incoming message you can use `message.answer(...)` alias
    # and the target chat will be passed to :ref:`aiogram.methods.send_message.SendMessage`
    # method automatically or call API method directly via
    # Bot instance: `bot.send_message(chat_id=message.chat.id, ...)`
    await message.answer(f"Hello, {html.bold(message.from_user.full_name)}!")


@dp.message(Command("prediction"))
async def choose_prediction(message: Message) -> None:
    user_id: int = message.from_user.id
    prediction: PredictionData = IN_MEMORY_PREDICTION_DB.get(user_id, None)
    if prediction is not None and prediction.expired_at > datetime.datetime.now():
        await message.reply_photo(FSInputFile(prediction.abs_file_path), caption="Твое маф будущее на сегодня и не пытайся это поменять")
    else:
        IN_MEMORY_PREDICTION_DB.pop(user_id, None)
        new_prediction_file = random.choice(os.listdir(PATH_TO_PREDICTION_MEMES))
        new_prediction = PredictionData(file_name=new_prediction_file, expired_at=datetime.datetime.now() + timedelta(seconds=PREDICTION_DURATION_IN_SECONDS))
        await message.reply_photo(FSInputFile(new_prediction.abs_file_path), caption="Мое предсказание для тебя")
        IN_MEMORY_PREDICTION_DB[user_id] = new_prediction




async def main() -> None:
    # Initialize Bot instance with default bot properties which will be passed to all API calls
    bot = Bot(token=TELEGRAM_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await bot.set_my_commands(commands=[BotCommand(command="prediction", description="Что тебя ждет сегодня?")])
    # And the run events dispatching
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())