from aiogram import types


async def set_default_commands(dp):
    await dp.bot.set_my_commands([
        types.BotCommand('start', 'start work bot'),
        types.BotCommand('info', 'displays all the cities that are in the bot')])
