import re
import datetime
import asyncio
from aiogram import Bot, types, Dispatcher, Executor

API_TOKEN = '123456789:AAG3xQ34X7m6XIa7Mc8ETU9_1iobqdRIXIU'

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot=bot)


class CallbackData:
    def __init__(self, prefix, *args):
        self.prefix = prefix
        self.args = args

    def new(self, *args):
        return self.__class__(self.prefix, *args)

    def __call__(self, *args, sep=':'):
        return f"{self.prefix}{sep}{''.join(str(arg) + sep for arg in args)}"


birthday_callback = CallbackData("set_birthday", "day", "month", "hour", "minute", "message")

birthday_messages = {}
allowed_users = {'756001144': True}
correct_invite_code = '14882281337'
user_access = {}


@dp.message_handler(commands=['help'])
async def show_commands(message: types.Message):
    commands = [
        '/help - Показать все доступные команды.',
        '/invite_code - Ввести пригласительный код.',
        '/set_message - Установить дату Дня Рождения и сообщение.',
        '/view_messages - Посмотреть все запланированные даты и сообщения.',
        '/del_message - Удалить выбранную дату и сообщение.'
    ]
    await message.answer('\n'.join(commands))


@dp.message_handler(commands=['invite_code'])
async def invite_code(message: types.Message):
    global user_access
    user_id = str(message.from_user.id)

    if user_id in allowed_users:
        await message.answer("Вы входите в список пользователей с привилегиями.")
        user_access[user_id] = True
        return

    input_code = message.get_args()
    if input_code == correct_invite_code:
        user_access[user_id] = True
        await message.reply("Код был принят. Заблокированная команда разблокирована.")
    else:
        await message.reply("Неправильный код.")


@dp.message_handler(commands=['set_message'])
async def set_message(message: types.Message):
    global user_access

    user_id = str(message.from_user.id)
    if user_id not in user_access or not user_access[user_id]:
        await message.reply("У Вас нет доступа для использования этой команды.")
        return

    text = message.get_args()
    match = re.match(r'^(\d{1,2})\.(\d{1,2}) (\d{1,2}):(\d{1,2}) (.+)', text)

    if match:
        day, month, hour, minute, birthday_message = match.groups()
        try:
            date = f'{int(day):02d}-{int(month):02d} {int(hour):02d}:{int(minute):02d}'
            datetime.datetime.strptime(date, '%d-%m %H:%M')
            if date in birthday_messages:
                await message.reply("Эта дата уже установлена.")
            else:
                birthday_messages[date] = birthday_message
                await message.reply("Дата и текст поздравления сохранены.")
        except ValueError:
            await message.reply("Некорректная дата.")
    else:
        await message.reply("Некорректный формат команды set_message.")


@dp.message_handler(commands=['view_messages'])
async def view_messages(message: types.Message):
    global user_access

    user_id = str(message.from_user.id)
    if user_id not in user_access or not user_access[user_id]:
        await message.reply("У Вас нет доступа для использования этой команды.")
        return

    if birthday_messages:
        for date, text in birthday_messages.items():
            await message.answer(f"Дата: {date}, Сообщение: {text}")
    else:
        await message.answer("Нет запланированных дат и сообщений.")


@dp.message_handler(commands=['del_message'])
async def delete_message(message: types.Message):
    global user_access

    user_id = str(message.from_user.id)
    if user_id not in user_access or not user_access[user_id]:
        await message.reply("У Вас нет доступа для использования этой команды.")
        return

    text = message.get_args()
    match = re.match(r'^(\d{1,2})\.(\d{1,2})', text)

    if match:
        day, month = match.groups()
        try:
            date = f'{int(day):02d}-{int(month):02d}'
            if date in birthday_messages:
                del birthday_messages[date]
                await message.reply("Выбранная дата и сообщение удалены.")
            else:
                await message.reply("Нет даты и сообщения для удаления.")
        except ValueError:
            await message.reply("Некорректная дата.")
    else:
        await message.reply("Некорректный формат команды del_message.")


async def send_birthday_messages():
    now = datetime.datetime.now().strftime("%d-%m %H:%M")
    for date, birthday_message in birthday_messages.items():
        if date == now:
            chat_id = '-4088949558'  # Замените на ID вашего чата
            await bot.send_message(chat_id, birthday_message)


async def check_birthday_messages():
    while True:
        await asyncio.sleep(60)  # Пауза в 60 секунд
        await send_birthday_messages()


if __name__ == '__main__':
    task = asyncio.ensure_future(check_birthday_messages())
    Executor(dp).start_polling(skip_updates=True, on_shutdown=task.cancel)
