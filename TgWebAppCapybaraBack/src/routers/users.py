from datetime import datetime, timedelta

from environs import Env
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_session
from src.schemas.users import UserRegisterSchema, UserWalletSchema, UserAcceptNft
from src.utils.users import get_user, create_user, increment_money, upgrade_lvl, notify_admin, nft_request, \
    get_all_requests_users, delete_nft_request, nft_accept

users_router = APIRouter()

env = Env()
env.read_env()

BOT_TOKEN = env('BOT_TOKEN')


@users_router.get("/{tg_id}")
async def get_user_route(tg_id: int, session: AsyncSession = Depends(get_session)):
    user = await get_user(session=session, tg_id=tg_id)
    if user:
        return user
    else:
        raise HTTPException(status_code=404, detail="Такого пользователя не существует")


@users_router.post("/login")
async def login_user_route(user: UserRegisterSchema, session: AsyncSession = Depends(get_session)):
    user_data = {
        "tg_id": user.tg_id,
        "fio": user.fio,
        "username": user.username,
    }

    user = await get_user(session=session, tg_id=user.tg_id)
    if user:
        return HTTPException(status_code=400, detail="Пользователь уже добавлен")
    else:
        new_user = await create_user(session, **user_data)
        if new_user:
            return new_user
        else:
            raise HTTPException(status_code=400, detail="Не удалось создать пользователя")


@users_router.put("/increment_money/{tg_id}/{count}")
async def increment_clicks_route(tg_id: int, count: float, session: AsyncSession = Depends(get_session)):
    user = await get_user(session=session, tg_id=tg_id)

    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    # current_time = datetime.now()

    if user.is_banned is not True:
        # if count > 200:
        #     user.is_banned = True
        #     await session.commit()
        #     raise HTTPException(status_code=403, detail="Пользователь забанен из-за чрезмерного количества кликов")

        new_count_money = await increment_money(session=session, user=user, count=count)
        # user.time_of_last_click = current_time
        await session.commit()
        return new_count_money

    else:
        user.is_banned = True
        await session.commit()
        raise HTTPException(status_code=403, detail="Пользователь забанен или слишком часто кликает")


@users_router.get("/lvl/{tg_id}")
async def get_lvl(tg_id: int, session: AsyncSession = Depends(get_session)):
    user = await get_user(session=session, tg_id=tg_id)
    if user:
        return user.lvl
    else:
        raise HTTPException(status_code=404, detail="Такого пользователя не существует")


@users_router.put("/upgrade/{tg_id}")
async def upgrade(tg_id: int, session: AsyncSession = Depends(get_session)):
    user = await get_user(session=session, tg_id=tg_id)

    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    if user.money < 15:
        raise HTTPException(status_code=401, detail="Не хватает денег")

    if user.lvl == 7:
        raise HTTPException(status_code=400, detail="Максимальный уровень")

    if not user.is_banned:
        # Текущее время UTC + 3 часа
        current_time = datetime.utcnow() + timedelta(hours=3)

        if user.last_upgrade:
            last_upgrade_moscow = user.last_upgrade + timedelta(hours=3)
            if current_time - last_upgrade_moscow < timedelta(days=1):
                raise HTTPException(status_code=403, detail="Уровень можно повысить только раз в день")

        new_user_lvl = await upgrade_lvl(session=session, user=user)
        user.last_upgrade = datetime.utcnow()  # Хранение времени в UTC

        await session.commit()
        return new_user_lvl

    else:
        user.is_banned = True
        await session.commit()
        raise HTTPException(status_code=403, detail="Пользователь забанен или слишком часто кликает")


@users_router.post("/nft_request")
async def nft_request_route(user: UserWalletSchema, session: AsyncSession = Depends(get_session)):
    db_user = await get_user(session=session, tg_id=user.tg_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    new_user = await nft_request(session, db_user, user.wallet)
    if new_user:
        await notify_admin(session, user.tg_id)
        return new_user
    else:
        raise HTTPException(status_code=400, detail="Не удалось создать пользователя")


@users_router.get("/all/requests")
async def get_all_requests_route(session: AsyncSession = Depends(get_session)):
    users = await get_all_requests_users(session=session)
    if users:
        return users
    else:
        raise HTTPException(status_code=404, detail="Неа")


@users_router.put("/delete/request/{tg_id}")
async def delete_request_route(tg_id: int, session: AsyncSession = Depends(get_session)):
    user = await get_user(session=session, tg_id=tg_id)

    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    if not user.is_banned:
        new_user_nft_request = await delete_nft_request(session=session, user=user)

        await session.commit()
        return new_user_nft_request

    else:
        user.is_banned = True
        await session.commit()
        raise HTTPException(status_code=403, detail="Пользователь забанен или слишком часто кликает")


@users_router.post("/accept/nft")
async def nft_request_route(user: UserAcceptNft, session: AsyncSession = Depends(get_session)):
    db_user = await get_user(session=session, tg_id=user.tg_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    new_user = await nft_accept(session, db_user, user.link, user.token)
    if new_user:
        return new_user
    else:
        raise HTTPException(status_code=400, detail="Не удалось создать пользователя")