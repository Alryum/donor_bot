import asyncio
import json
from aiogram import Bot, Dispatcher, types
from dotenv import load_dotenv
import logging
import os

from parser import get_free_days


load_dotenv()
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')
REGULAR_PASSWORD = os.getenv('REGULAR_PASSWORD')
TOKEN = os.getenv('TG_BOT_TOKEN')
CHECK_INTERVAL = 60  # 10 минут
regular_users = set()
admin_users = set()


def save_users():
    """Сохраняет пользователей в файл"""
    data = {
        'regular_users': list(regular_users),
        'admin_users': list(admin_users)
    }
    with open('users.json', 'w') as f:
        json.dump(data, f)


def load_users():
    """Загружает пользователей из файла"""
    try:
        with open('users.json', 'r') as f:
            data = json.load(f)
            regular_users.update(data.get('regular_users', []))
            admin_users.update(data.get('admin_users', []))
    except FileNotFoundError:
        pass


load_users()
bot = Bot(token=TOKEN)
dp = Dispatcher()


@dp.message()
async def login_cmd(message: types.Message):
    user_id = message.from_user.id

    try:
        password = message.text.split()[1]
    except IndexError:
        await message.answer("Использование: /login пароль")
        return

    if password == ADMIN_PASSWORD:
        if user_id not in admin_users:
            admin_users.add(user_id)
            await message.answer("✅ Вы вошли как администратор!")
        else:
            await message.answer("Уже авторизованы как админ.")

    elif password == REGULAR_PASSWORD:
        if user_id not in regular_users:
            regular_users.add(user_id)
            await message.answer("✅ Вы подписаны на уведомления!")
        else:
            await message.answer('Вы уже подписаны на рассылку.')

    else:
        await message.answer("❌ Неверный пароль!")
        return

    save_users()


async def send_to_all_users(text: str):
    for user_id in regular_users:
        try:
            await bot.send_message(user_id, text)
        except Exception:
            pass


async def send_to_admins(text: str):
    for user_id in admin_users:
        try:
            await bot.send_message(user_id, text)
        except Exception:
            pass


async def notify_users():
    while True:
        try:
            free_days = await get_free_days()
            formatted_free_days = "\n".join(f"• {day}" for day in free_days)
            if free_days:
                await send_to_all_users(formatted_free_days)
            else:
                await send_to_all_users('Доступных записей не найдено.')
        except Exception as e:
            logging.error(f"Ошибка при проверке сайта: {e}")
            message = f"""❌ *Ошибка при проверке сайта*

```python
{str(e)}
```"""
            await send_to_admins(message)

        await asyncio.sleep(CHECK_INTERVAL)


async def main():
    asyncio.create_task(notify_users())
    await dp.start_polling(bot)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
