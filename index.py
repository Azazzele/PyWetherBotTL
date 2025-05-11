import os
import logging
import asyncio
import sys
from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message
from dotenv import load_dotenv
from geopy.geocoders import Nominatim
import aiohttp

# Загружаем переменные окружения
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("WEATHER_TOKEN")

# Проверка токенов
if not TOKEN or not API_KEY:
    raise ValueError("BOT_TOKEN или WEATHER_TOKEN не указаны в .env файле!")

dp = Dispatcher()



@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(
        f"Привет, {html.bold(message.from_user.full_name)}! "
        "Напиши название города, и я покажу тебе погоду ☀️"
    )



@dp.message()
async def weather_handler(message: Message) -> None:
    city_name = message.text.strip().replace("погода в", "").replace("погода", "").strip()

    if not city_name:
        await message.answer("Введите название города.")
        return

    geolocator = Nominatim(user_agent="weather_bot")

    try:
        locations = geolocator.geocode(city_name, country_codes="RU", exactly_one=False)

        if not locations:
            await message.answer(f"Не найдено результатов по запросу: {city_name}")
            return

        reply_lines = []
        selected_location = None

        for i, loc in enumerate(locations[:10], 1):
            if city_name.lower() in loc.address.lower():
                reply_lines.append(f"{i}. 📍 <b>{loc.address}</b>")
                if not selected_location:
                    selected_location = loc

        if not reply_lines:
            await message.answer("Совпадения найдены, но ни одно не соответствует точному городу.")
            return


        # Получаем и отправляем погоду
        if selected_location:
            lat, lon = selected_location.latitude, selected_location.longitude

            url = (
                f"http://api.openweathermap.org/data/2.5/weather"
                f"?lat={lat}&lon={lon}&appid={API_KEY}&units=metric&lang=ru"
            )

            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        await message.answer("❌ Ошибка при получении погоды.")
                        return
                    data = await response.json()

            description = data["weather"][0]["description"].capitalize()
            temp = data["main"]["temp"]
            feels_like = data["main"]["feels_like"]
            humidity = data["main"]["humidity"]
            wind_speed = data["wind"]["speed"]

            await message.answer(
                f"🌦 Погода в <b>{city_name}</b>:\n"
                f"🌡 Температура: <b>{temp}°C</b> (ощущается как {feels_like}°C)\n"
                f"💧 Влажность: {humidity}%\n"
                f"💨 Ветер: {wind_speed} м/с\n"
                f"☁️ Состояние: {description}"
            )

    except Exception as e:
        logging.exception("Ошибка при получении погоды:")
        await message.answer("Произошла ошибка при обработке. Попробуйте позже.")



# Основная функция запуска бота
async def main() -> None:
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
