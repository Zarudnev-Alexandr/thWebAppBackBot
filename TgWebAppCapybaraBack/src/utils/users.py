from datetime import datetime
from typing import Type

import aiohttp
from environs import Env
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import User

env = Env()
env.read_env()

BOT_TOKEN = env('BOT_TOKEN')
ADMIN_ID = env('ADMIN_ID')


async def get_user(session: AsyncSession, tg_id: int) -> Type[User] | None:
    user = await session.get(User, tg_id)
    return user


async def create_user(session: AsyncSession, **kwargs) -> User:
    user_data = kwargs

    user = User(**user_data)
    session.add(user)
    await session.commit()
    return user


async def increment_money(session: AsyncSession, user, count):
    user.money += count

    await session.commit()
    return user.money


async def upgrade_lvl(session: AsyncSession, user):
    user.lvl += 1
    user.money -= 15
    await session.commit()
    return user


async def notify_admin(session: AsyncSession, user_tg_id: int):
    user = await get_user(session, user_tg_id)
    if user:
        async with aiohttp.ClientSession() as session1:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            payload = {
                "chat_id": ADMIN_ID,
                "text": f"Пользователь {user.fio}, оставил заявку на получение nft.\nНажмите на 'Заявки' в главном "
                        f"меню. Чтобы его вызвать - /start"
            }
            async with session1.post(url, json=payload) as response:
                if response.status != 200:
                    print(f"Failed to send notification: {response.status}")


async def nft_request(session: AsyncSession, user, wallet):
    user.wallet = wallet
    user.nft_request = True
    await session.commit()
    return user


async def get_all_requests_users(session: AsyncSession):
    result = await session.execute(
        select(User)
        .where(User.nft_request == True)
    )

    users = result.scalars().all()
    users_data = [
        (item.fio, int(item.tg_id)) for item in users
    ]
    print(users_data)
    return {'requests': users_data}


async def delete_nft_request(session: AsyncSession, user,):
    user.nft_request = False
    await session.commit()
    return user


async def nft_accept(session: AsyncSession, user, link, token):
    user.nft_link = link
    user.nft_token = token
    user.nft_request = False
    user.is_get_nft = True
    await session.commit()
    return user
