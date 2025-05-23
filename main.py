import asyncio
import datetime
import logging
import os
import random
import sys
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import assert_never

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
PATH_TO_PREDICTION_FILE = os.getenv(f"{ENV_PREFIX}PATH_TO_PREDICTION_FILE", "./predictions.txt")
ONLY_TEXT_PREDICTIONS = bool(os.getenv(f"{ENV_PREFIX}ONLY_TEXT_PREDICTIONS", True))
PREDICTIONS_DROP_AT = datetime.time.fromisoformat(os.getenv(f"{ENV_PREFIX}PREDICTIONS_DROP_AT", "06:00"))

# All handlers should be attached to the Router (or Dispatcher)
dp = Dispatcher()

class PredictionTypes(Enum):
    text = auto()
    file = auto()

@dataclass
class PredictionData:
    created_at: datetime.datetime = field(default_factory=datetime.datetime.now)
    file_name: str | None = None
    phrase: str | None = None

    @property
    def abs_file_path(self) -> Path:
        return Path(PATH_TO_PREDICTION_MEMES, self.file_name).resolve()

    @property
    def prediction_type(self) -> PredictionTypes:
        return PredictionTypes.text if self.phrase is not None else PredictionTypes.file

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
    datetime_now: datetime.datetime = datetime.datetime.now()
    date_now: datetime.date = datetime_now.date()
    drop_time = datetime.datetime(date_now.year, date_now.month, date_now.day, hour=PREDICTIONS_DROP_AT.hour, minute=PREDICTIONS_DROP_AT.minute)
    if prediction is not None and (datetime_now < drop_time or prediction.created_at > drop_time):
        match prediction.prediction_type:
            case PredictionTypes.text:
                await message.reply(text=prediction.phrase)
            case PredictionTypes.file:
                await message.reply_photo(FSInputFile(prediction.abs_file_path), caption="Твое маф будущее на сегодня и не пытайся это поменять")
            case _ as unreachable:
                assert_never(unreachable)
    else:
        IN_MEMORY_PREDICTION_DB.pop(user_id, None)
        prediction_type = PredictionTypes.text if ONLY_TEXT_PREDICTIONS else random.choice(list(PredictionTypes))
        match prediction_type:
            case PredictionTypes.text:
                with open(Path(PATH_TO_PREDICTION_FILE).resolve()) as f:
                    # Каждый раз открываю файл что бы не перезагружать (и не сбрасывать предсказания соответсвенно) если нужно добавить еще предсказаний
                    text_prediction = random.choice([l for l in f.readlines()])
                new_prediction = PredictionData(phrase=text_prediction)
                await message.reply(text=new_prediction.phrase)
            case PredictionTypes.file:
                new_prediction_file = random.choice(os.listdir(PATH_TO_PREDICTION_MEMES))
                new_prediction = PredictionData(file_name=new_prediction_file)
                await message.reply_photo(FSInputFile(new_prediction.abs_file_path), caption="Мое предсказание для тебя")
            case _ as unreachable:
                assert_never(unreachable)
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