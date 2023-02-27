from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def start_user():
    btnMagnit = InlineKeyboardButton(text='scrape magnit', callback_data='scrape_magnit')
    menu = InlineKeyboardMarkup(1)
    menu.insert(btnMagnit)
    return menu
