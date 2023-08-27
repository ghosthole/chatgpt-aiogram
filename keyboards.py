from aiogram import types


menu_keyboard = types.InlineKeyboardMarkup(row_width=2)
menu_keyboard.add(types.InlineKeyboardButton(text="Профиль", callback_data="profile"),
                  types.InlineKeyboardButton(text="Чат-бот", callback_data="chat-bot"))
menu_keyboard.add(types.InlineKeyboardButton(text="Генерация картинки", callback_data="generate_photo"))
back_to_menu_keyboard = types.InlineKeyboardMarkup(row_width=1)
back_to_menu_keyboard.add(types.InlineKeyboardButton(text="Назад", callback_data="back_to_menu"))
