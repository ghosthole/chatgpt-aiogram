from aiogram import Bot, Dispatcher, executor
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types.callback_query import CallbackQuery
from aiogram.dispatcher.filters.state import State, StatesGroup
from dotenv import load_dotenv
from keyboards import *
import sqlite3 as sql
import os
import openai


def create_table():
    cur.execute("""CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT,
    user_id INTEGER,
    quantity_entry INTEGER,
    quantity_requests INTEGER);
    """)


with sql.connect(database="chatgpt.db") as con:
    cur = con.cursor()
    create_table()


class RequestWaitChatBot(StatesGroup):
    wait_for_request_chat_bot = State()


class RequestWaitGeneratePhoto(StatesGroup):
    wait_for_request_generate_photo = State()


load_dotenv()
bot = Bot(token=os.getenv("TOKEN"), parse_mode="HTML")
dp = Dispatcher(bot=bot, storage=MemoryStorage())
openai.api_key = os.getenv("OPENAI_KEY")


@dp.message_handler(commands="start")
async def start_bot(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.first_name
    id_user = cur.execute("""SELECT user_id FROM users WHERE user_id = ?""", (user_id,))
    if id_user.fetchone() is None:
        cur.execute("""INSERT INTO users (username, user_id, quantity_entry, quantity_requests)
        VALUES (?, ?, ?, ?)""", (username, user_id, 0, 0))
        con.commit()
    cur.execute("""UPDATE users SET quantity_entry = quantity_entry + 1 WHERE user_id = ?""", (user_id,))
    con.commit()
    quantity_entry = cur.execute("""SELECT quantity_entry FROM users WHERE user_id = ?""", (user_id,))
    if quantity_entry.fetchone()[0] == 1:
        await message.answer(text=f'''{username}! Мы тебя здесь не видели
Хочешь воспользоваться моими возможностями? Тогда нажми на кнопку "Активировать" ниже!''', reply_markup=menu_keyboard)
    else:
        await message.answer(text=f'''{username}! Ты снова у нас! Чем помочь тебе в этот раз?''',
                             reply_markup=menu_keyboard)


async def chat_bot(callback: CallbackQuery, state: FSMContext):
    global msg
    await callback.message.delete()
    await callback.answer()
    msg = await callback.message.answer(text="""Отлично, теперь тебе нужно ввести запрос.""")
    await state.set_state(RequestWaitChatBot.wait_for_request_chat_bot.state)


async def send_request(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    cur.execute("""UPDATE users SET quantity_requests = quantity_requests + 1 WHERE user_id = ?""",
                (user_id,))
    con.commit()
    await msg.delete()
    wait_message = await message.answer(text="Ответ загружается...")
    await state.update_data(request=message.text)
    request_user = await state.get_data()
    await state.finish()
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": request_user["request"]}
        ]
    )
    await wait_message.delete()
    await message.answer(text=completion.choices[0].message.content, reply_markup=back_to_menu_keyboard)


@dp.callback_query_handler(text="back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    await callback.message.delete()
    await callback.answer()
    await callback.message.answer(text="Ты вернулся в меню. Чем могу помочь сейчас?", reply_markup=menu_keyboard)


async def profile(callback: CallbackQuery):
    user_id = callback.from_user.id
    username = callback.from_user.first_name
    quantity_requests = cur.execute("""SELECT quantity_requests FROM users WHERE user_id = ?""",
                                    (user_id,)).fetchone()
    await callback.answer()
    await callback.message.delete()
    await callback.message.answer(text=f"""
╔PROFILE
║
╠NAME: {username}
║
╠ID: {user_id}
║
╠REQUESTS: {quantity_requests[0]}
""", reply_markup=menu_keyboard)


async def generate_photo(callback: CallbackQuery, state: FSMContext):
    global msg
    await callback.message.delete()
    msg = await callback.message.answer("Отлично, теперь напиши запрос для создания картинки.")
    await state.set_state(RequestWaitGeneratePhoto.wait_for_request_generate_photo.state)


async def send_photo(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    cur.execute("""UPDATE users SET quantity_requests = quantity_requests + 1 WHERE user_id = ?""",
                (user_id,))
    con.commit()
    await msg.delete()
    wait_message = await message.answer("Картинка загружаются...")
    await state.update_data(request=message.text)
    request_user = await state.get_data()
    response = openai.Image.create(
        prompt=request_user["request"],
        n=1,
        size="1024x1024"
    )
    await wait_message.delete()
    await message.answer_photo(response["data"][0]["url"], reply_markup=menu_keyboard)


def create_handlers():
    dp.register_callback_query_handler(callback=chat_bot, text="chat-bot", state="*")
    dp.register_message_handler(callback=send_request, state=RequestWaitChatBot.wait_for_request_chat_bot)
    dp.register_callback_query_handler(callback=generate_photo, text="generate_photo", state="*")
    dp.register_message_handler(callback=send_photo, state=RequestWaitGeneratePhoto)
    dp.register_callback_query_handler(callback=profile, text="profile", state="*")


if __name__ == "__main__":
    create_handlers()
    executor.start_polling(dp, skip_updates=True)
