from config import TOKEN, WEATHER_API_KEY
import asyncio
from aiogram import Bot, Dispatcher, Router, types
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.fsm.storage.memory import MemoryStorage
import requests
import os
from aiogram.types import FSInputFile  # Добавляем импорт для работы с файлами
from gtts import gTTS  # Для генерации голосового сообщения
from googletrans import Translator
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
import sqlite3

# Настройка хранилища
storage = MemoryStorage()

# Создание бота
bot = Bot(token=TOKEN)

# Создание диспетчера
dp = Dispatcher(storage=storage)

# Создание роутера
router = Router()

# Регистрация роутера в диспетчере
dp.include_router(router)

# Обработчик команды /start
@router.message(CommandStart())
async def start(message: Message):
    await message.answer("Приветики, я бот!")

# Определяем состояния для машины состояний
class StudentForm(StatesGroup):
    name = State()
    age = State()
    grade = State()

# Обработчик команды /add_student
@router.message(Command("add_student"))
async def add_student(message: Message, state: FSMContext):
    await message.answer("Введите имя ученика:")
    await state.set_state(StudentForm.name)

# Обработчик ввода имени
@router.message(StudentForm.name)
async def enter_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Введите возраст ученика:")
    await state.set_state(StudentForm.age)

# Обработчик ввода возраста
@router.message(StudentForm.age)
async def enter_age(message: Message, state: FSMContext):
    try:
        age = int(message.text)
        await state.update_data(age=age)
        await message.answer("Введите класс ученика:")
        await state.set_state(StudentForm.grade)
    except ValueError:
        await message.answer("Возраст должен быть числом. Попробуйте снова.")

# Обработчик ввода класса
@router.message(StudentForm.grade)
async def enter_grade(message: Message, state: FSMContext):
    user_data = await state.get_data()
    name = user_data.get("name")
    age = user_data.get("age")
    grade = message.text

    # Сохраняем данные в базу данных
    try:
        conn = sqlite3.connect('school_data.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO students (name, age, grade) VALUES (?, ?, ?)", (name, age, grade))
        conn.commit()
        conn.close()

        await message.answer(f"Данные ученика сохранены:\nИмя: {name}\nВозраст: {age}\nКласс: {grade}")
    except Exception as e:
        print(f"Ошибка при сохранении данных: {e}")
        await message.answer("Произошла ошибка при сохранении данных.")

    # Завершаем работу состояния
    await state.clear()



# Обработчик команды /see_bd
@router.message(Command("see_bd"))
async def see_bd(message: Message):
    try:
        # Подключаемся к базе данных
        conn = sqlite3.connect('school_data.db')
        cursor = conn.cursor()

        # Получаем данные из таблицы students
        cursor.execute("SELECT * FROM students")
        rows = cursor.fetchall()
        conn.close()

        # Проверяем, есть ли данные
        if not rows:
            await message.answer("В базе данных пока нет записей.")
            return

        # Формируем сообщение с данными
        response_message = "Список учеников:\n"
        for row in rows:
            student_id, name, age, grade = row
            response_message += f"ID: {student_id}, Имя: {name}, Возраст: {age}, Класс: {grade}\n"

        # Отправляем данные пользователю
        await message.answer(response_message)
    except Exception as e:
        print(f"Ошибка при чтении базы данных: {e}")
        await message.answer("Произошла ошибка при получении данных из базы.")




# Обработчик команды /help
@router.message(Command("help"))
async def help_command(message: Message):
    await message.answer("Я умею говорить!")

# Обработчик команды /pogoda
@router.message(Command("pogoda"))
async def weather_command(message: Message):
    city_name = "Moscow"  # Название города
    units = "metric"  # Единицы измерения
    response_message = get_weather(city_name, units)
    await message.answer(response_message)


# Обработчик команды /voice
@router.message(Command("voice"))
async def send_voice(message: Message):
    try:
        # Текст для голосового сообщения
        text = "Приветики, я бот! Это тестовое голосовое сообщение."

        # Проверка текста
        if not text.strip():
            raise ValueError("Текст для синтеза пустой!")

        # Генерация голосового сообщения
        voice_file_path = "sample.ogg"
        print("Начинаю генерацию голосового сообщения...")
        tts = gTTS(text=text, lang="ru")
        tts.save(voice_file_path)  # Сохраняем файл
        print(f"Файл {voice_file_path} успешно сохранён.")

        # Проверка: был ли создан файл
        if not os.path.exists(voice_file_path):
            raise FileNotFoundError("Файл голосового сообщения не был создан!")

        # Проверка: файл не пустой
        if os.path.getsize(voice_file_path) == 0:
            raise ValueError("Сгенерированный аудиофайл пустой!")

        # Отправляем голосовое сообщение
        print(f"Отправляю голосовое сообщение: {voice_file_path}")
        voice = FSInputFile(voice_file_path)
        await message.answer_voice(voice)

        # # Удаляем файл после отправки пока закоментирую
        # os.remove(voice_file_path)
        # print(f"Файл {voice_file_path} успешно удалён.")

        # Уведомляем об успешной отправке
        await message.answer("Голосовое сообщение отправлено!")
    except Exception as e:
        # Логируем ошибку и уведомляем пользователя
        print(f"Ошибка при создании голосового сообщения: {e}")
        await message.answer("Произошла ошибка при создании голосового сообщения.")



# Обработчик фото
@router.message(lambda message: message.photo)
async def handle_photo(message: Message):
    # Проверяем и создаем папку img, если ее нет
    if not os.path.exists("img"):
        os.makedirs("img")

    # Получаем лучшее качество фото
    photo = message.photo[-1]  # Фото с наивысшим разрешением

    # Получаем файл через API Telegram
    file = await bot.get_file(photo.file_id)

    # Устанавливаем путь для сохранения фото
    file_path = f"img/{photo.file_id}.jpg"

    # Сохраняем фото
    await bot.download_file(file.file_path, destination=file_path)

    await message.answer("Фото сохранено!")


# Функция для получения погоды
def get_weather(city_name, units):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={WEATHER_API_KEY}&units={units}"
    response = requests.get(url)
    data = response.json()
    if response.status_code == 200:
        return (
            f"Погода в {city_name}:\n"
            f"Температура: {data['main']['temp']}°C\n"
            f"Влажность: {data['main']['humidity']}%\n"
            f"Описание: {data['weather'][0]['description']}"
        )
    else:
        return f"Ошибка: {data.get('message', 'Неизвестная ошибка')}"


# Создаем объект Translator
translator = Translator()

@router.message()
async def translate_text(message: Message):
    try:
        # Проверяем, является ли текст командой
        if message.text.startswith('/'):
            return  # Если это команда, ничего не делаем

        # Получаем текст пользователя
        user_text = message.text

        # Переводим текст на английский
        translated = translator.translate(user_text, src="auto", dest="en")

        # Отправляем переведенный текст пользователю
        await message.answer(f"Перевод на английский:\n{translated.text}")
    except Exception as e:
        print(f"Ошибка при переводе текста: {e}")
        await message.answer("Произошла ошибка при переводе текста.")






# Основная функция
async def main():
    print("Bot is running")
    await dp.start_polling(bot)

# Исполнение программы
if __name__ == "__main__":
    asyncio.run(main())
