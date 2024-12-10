from config import TOKEN
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.fsm.storage.memory import MemoryStorage
import requests

WEATHER_API_KEY = '528030aee6c1dde045f8383c4cfd14a9'
WEATHER_URL = 'http://api.openweathermap.org/data/2.5/weather'


# Настройка хранилища
storage = MemoryStorage()

# Создание бота
bot = Bot(token=TOKEN)

# Создание диспетчера
dp = Dispatcher(storage=storage)

# Обработчик команды /start
@dp.message(CommandStart())
async def start(message: Message):
    await message.answer("Приветики, я бот!")

# Обработчик команды /help
@dp.message(Command('help'))
async def help(message: Message):
    await message.answer("Я умею говорить")

# Обработчик команды /pogoda
@dp.message(Command('pogoda'))
async def help(message: Message):
    city_name = 'Moscow'  # Название города
    units = 'metric'  # Единицы измерения
    mypogoda(city_name,units)
    mymessage = mypogoda(city_name,units)
    print(mymessage)
    await message.answer(mymessage)


city_name = 'Moscow'  # Название города
units = 'metric'  # Единицы измерения

url = f'http://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={WEATHER_API_KEY}&units={units}'

response = requests.get(url)
data = response.json()

if response.status_code == 200:
    print(f"Погода в {city_name}:")
    print(f"Температура: {data['main']['temp']}°C")
    print(f"Влажность: {data['main']['humidity']}%")
    print(f"Описание: {data['weather'][0]['description']}")
else:
    print(f"Ошибка: {data['message']}")


def mypogoda(city_name,units):
    url = f'http://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={WEATHER_API_KEY}&units={units}'
    response = requests.get(url)
    data = response.json()
    stroka = ''
    if response.status_code == 200:
        stroka = f"Погода в {city_name}: \nТемпература: {data['main']['temp']}°C \nВлажность: {data['main']['humidity']}% \nОписание: {data['weather'][0]['description']}"

    else:
        stroka = f"Ошибка: {data['message']}"

    return stroka


# Основная функция
async def main():
    print("Bot is running")
    await dp.start_polling(bot)

# Исполнение программы
if __name__ == "__main__":
    asyncio.run(main())