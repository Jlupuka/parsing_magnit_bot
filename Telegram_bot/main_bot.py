import logging
from os import getenv

from aiofiles import os
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.utils.markdown import hbold, hlink
from dotenv import load_dotenv

from hendlers import murk_up
from scrape_magnit.main import collect_data
from states.state_city import Register

logging.basicConfig(level=logging.INFO)

load_dotenv()

bot = Bot(token=getenv('TOKEN'))
dp = Dispatcher(bot, storage=MemoryStorage())

city_code_dict = {
    'Москва': '2398',
    'Екатеринбург': '1869',
    'Оренбург': '2403',
    'Казань': '2076',
    'Краснодар': '1761',
    'Санкт-Петербург': '1645',
    'Челябинск': '2001',
    'Новосибирск': '2425',
    'Орск': '2407',
    'Абдулино': '12733',
    'Шевченко': '12971',
    'Новотроицк': '2406'
}


async def on_startup(dispatcher):
    from bot_commands.commands import set_default_commands
    await set_default_commands(dispatcher)
    print("Бот запущен!")


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer(text='Please select a shop', reply_markup=murk_up.start_user())


@dp.message_handler(commands=['info'])
async def info(message: types.Message):
    all_city = '\n'.join(hbold(city) for city in city_code_dict.keys())
    await message.answer(text=all_city, parse_mode='HTML')


@dp.callback_query_handler(text="scrape_magnit")
async def scrape_magnit(callback: types.CallbackQuery):
    text = 'Please write the name of the city in Russian, for example: Москва'
    await bot.send_message(chat_id=callback.from_user.id, text=text)
    await Register.city.set()


@dp.message_handler(state=Register.city)
async def send_data(message: types.Message, state: FSMContext):
    city_code = city_code_dict.get(message.text)
    if city_code:
        text = f"{hbold('Please waiting 30-300 sec.')}"
        await bot.send_message(chat_id=message.from_user.id,
                               text=text, parse_mode='HTML')
        await state.finish()
        file = await collect_data(city_code=city_code)
        await bot.send_document(chat_id=message.from_user.id, document=open(file, 'rb'))
        await os.remove(file)
    else:
        text = f"{hbold('В нашей базе данных нет такого города')}. " \
               f"Проверьте актуальные города с помощью команды /info" \
               f" За подробной информацией обратитесь к {hlink('администратору', 'https://t.me/to4ka_py')} бота"
        await bot.send_message(chat_id=message.from_user.id, text=text, reply_markup=murk_up.start_user(),
                               parse_mode='HTML')
        await state.finish()


if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup)
