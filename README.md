# mafia_prediction_telegram_bot

Шуточный бот с предсказаниями. Просто возвращает случайную картинка из ротированных 
в директории (по дефолту `./prediction_memes`). Предсказание лочится за пользователем на n
секунд

Виртуальное окружение управляется с помощью [uv](https://docs.astral.sh/uv/#installation)

Запуск бота `pytohn ./main.py`

## Настройки

Настройки в бота передаются с помощью переменых окружения

- MAFIA_PREDICTION_BOT_TELEGRAM_TOKEN - телеграм токен для бота
- MAFIA_PREDICTION_BOT_PATH_TO_PREDICTION_MEMES - путь к дериктории с картинками, default - `./prediction_memes`
- MAFIA_PREDICTION_BOT_PREDICTION_DURATION_IN_SECONDS - блокировка предсказания в секундах, default - `86400`