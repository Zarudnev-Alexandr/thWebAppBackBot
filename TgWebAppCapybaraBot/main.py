from typing import Any

import requests
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode, ContentType
from aiogram.filters import CommandStart
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, User, CallbackQuery
from aiogram.utils.callback_answer import CallbackAnswerMiddleware
from aiogram_dialog import DialogManager, StartMode, setup_dialogs, Dialog, Window
from aiogram_dialog.widgets.input import TextInput, MessageInput, ManagedTextInput
from aiogram_dialog.widgets.kbd import Url, WebApp, Button, ScrollingGroup, Select, Back, Row, Next
from aiogram_dialog.widgets.text import Const, Format
from environs import Env

env = Env()
env.read_env()

BOT_TOKEN = env('BOT_TOKEN')
API_URL = env('API_URL')

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()


class StartSG(StatesGroup):
    start = State()


class AllRequestsSG(StatesGroup):
    start = State()
    request_info = State()
    enter_nft = State()
    enter_link = State()
    accept = State()


async def get_user(event_from_user: User, dialog_manager: DialogManager, **kwargs):
    tg_id = event_from_user.id

    try:
        user_response = requests.get(f'{API_URL}users/{tg_id}')

        if user_response.status_code == 200:
            user_data = user_response.json()
        else:
            user_data = None

        if not user_data:
            return {'new_user': True, 'username': event_from_user.username}

        if user_data.get('is_admin'):
            return {'admin': True, 'username': event_from_user.username, }
        return {'old_user': True, 'username': event_from_user.username}

    except requests.RequestException as e:
        print(f"Error fetching user data: {e}")
        return {'error': 'Error fetching user data'}


async def get_requests(dialog_manager: DialogManager, **kwargs):
    try:
        all_requests_response = requests.get(f'{API_URL}users/all/requests')

        if all_requests_response.status_code == 200:
            all_requests_data = all_requests_response.json()
            print(all_requests_data)
        else:
            all_requests_data = None
        return {'all_requests_data': all_requests_data['requests']}

    except requests.RequestException as e:
        print(f"Error fetching user data: {e}")
        return {'error': 'Error fetching user data'}


async def get_request_info(event_from_user: User, dialog_manager: DialogManager, **kwargs):
    ctx = dialog_manager.current_context()
    request_id = int(ctx.dialog_data['selected_request_id'])

    user_response = requests.get(f'{API_URL}users/{request_id}')

    if user_response.status_code == 200:
        user_data = user_response.json()

        return {'username': user_data.get('username'),
                'fio': user_data.get('fio'),
                'wallet': user_data.get('wallet')}


async def del_request(callback: CallbackQuery,
                   button: Button,
                   dialog_manager: DialogManager):

    ctx = dialog_manager.current_context()
    request_id = int(ctx.dialog_data['selected_request_id'])

    requests.put(f'{API_URL}users/delete/request/{request_id}')

    ctx.dialog_data.update(selected_film_id='')
    await dialog_manager.back()


async def accept_nft_link(event_from_user: User, dialog_manager: DialogManager, **kwargs):
    ctx = dialog_manager.current_context()
    request_id = int(ctx.dialog_data['selected_request_id'])
    nft_shop_link = str(ctx.dialog_data['nft_shop_link'])
    nft_token = str(ctx.dialog_data['nft_token'])

    payload = {
        'tg_id': request_id,
        'link': nft_shop_link,
        'token': nft_token
    }

    try:
        response = requests.post(f'{API_URL}users/accept/nft', json=payload)

        if response.status_code == 200:
            user_data = response.json()
            ctx.dialog_data.update(selected_request_id='')
            ctx.dialog_data.update(nft_shop_link='')
            return {'nft_shop_link': user_data.get('nft_link'), 'nft_token': user_data.get('nft_token')}
        else:
            print(f"Error: {response.status_code} - {response.json().get('detail')}")

    except requests.RequestException as e:
        print(f"Error making POST request: {e}")


async def request_selection(
        callback: CallbackQuery,
        widget: Select,
        manager: DialogManager,
        item_id: str
):
    ctx = manager.current_context()
    ctx.dialog_data.update(selected_request_id=item_id)
    await manager.switch_to(AllRequestsSG.request_info)


async def switch_to_get_requests(
        callback: CallbackQuery,
        button: Button,
        dialog_manager: DialogManager
):
    await dialog_manager.done()
    await dialog_manager.start(state=AllRequestsSG.start)


async def switch_to_main_menu(
        callback: CallbackQuery,
        button: Button,
        dialog_manager: DialogManager
):
    await dialog_manager.done()
    await dialog_manager.start(state=StartSG.start)


async def no_text(message: Message, widget: MessageInput, dialog_manager: DialogManager):
    await message.answer(text='Вы ввели вообще не текст!')


async def close_dialog(
        callback: CallbackQuery,
        button: Button,
        dialog_manager: DialogManager
):
    await dialog_manager.done()
    await dialog_manager.start(state=StartSG.start)


def name_check(text: Any) -> str:
    if 1 <= len(text) <= 250:
        return text
    raise ValueError


async def correct_film_name_handler(
        message: Message,
        widget: ManagedTextInput,
        dialog_manager: DialogManager,
        text: str) -> None:
    dialog_manager.dialog_data['nft_shop_link'] = text
    await dialog_manager.next()


async def correct_nft_name_handler(
        message: Message,
        widget: ManagedTextInput,
        dialog_manager: DialogManager,
        text: str) -> None:
    dialog_manager.dialog_data['nft_token'] = text
    await dialog_manager.next()


async def error_film_handler(
        message: Message,
        widget: ManagedTextInput,
        dialog_manager: DialogManager,
        error: ValueError):
    await message.answer(
        text='Вы ввели некорректное название. Попробуйте еще раз'
    )


@dp.message(CommandStart())
async def command_start_process(message: Message, dialog_manager: DialogManager):
    await dialog_manager.start(state=StartSG.start, mode=StartMode.RESET_STACK)


start_dialog = Dialog(
    Window(
        Format('Привет, {username}!'),
        Format('Никогда не пользовался нашим ботом? Сейчас исправим,\n Просто нажми на кнопку снизу и произойдет '
               'автоматическая регистрация', when='new_user'),
        Format('У тебя есть админские права', when='admin'),
        Format('C возвращением!', when='old_user'),
        WebApp(Const('Играть'), Const('https://a97e-194-87-199-70.ngrok-free.app')),
        Button(Const('Заявки'), id='zayavki', when='admin', on_click=switch_to_get_requests),
        getter=get_user,
        state=StartSG.start
    )
)

watch_all_requests_dialog = Dialog(
    Window(
        Const(text='Выбери заявку от пользователя:'),
        ScrollingGroup(
            Select(
                Format('{item[0]}'),
                id='zayavka',
                item_id_getter=lambda x: x[1],
                items='all_requests_data',
                on_click=request_selection,
            ),
            width=1,
            id='films_scrolling_group',
            height=6,
        ),
        Button(Const('📃В главное меню'), id='to_main_menu', on_click=switch_to_main_menu),
        state=AllRequestsSG.start,
        getter=get_requests
    ),
    Window(
        Format(text='Заявка от: <b>{fio}</b>\n'
                    '{username}\n\n'
                    'Кошелек: {wallet}'),
        Row(
            Back(Const('◀️назад'), id='back2'),
            Next(Const('✅Одобрить заявку'), id='accept_request'),
            Button(Const(text='❌Отклонить заявку'), id='del_request', on_click=del_request)
        ),
        getter=get_request_info,
        state=AllRequestsSG.request_info
    ),
    Window(
        Const(text='Введи nft'),
        TextInput(
            id='nft_input',
            type_factory=name_check,
            on_success=correct_nft_name_handler,
            on_error=error_film_handler,
        ),
        MessageInput(
            func=no_text,
            content_types=ContentType.ANY
        ),
        Button(Const('Отмена❌'), id='button_cancel', on_click=close_dialog),
        state=AllRequestsSG.enter_nft,
    ),
    Window(
        Const(text='Введи ссылку на нфт в магазине'),
        TextInput(
            id='link_input',
            type_factory=name_check,
            on_success=correct_film_name_handler,
            on_error=error_film_handler,
        ),
        MessageInput(
            func=no_text,
            content_types=ContentType.ANY
        ),
        Button(Const('Отмена❌'), id='button_cancel', on_click=close_dialog),
        state=AllRequestsSG.enter_link,
    ),
    Window(
        Format(text='Ссылка: {nft_shop_link}\nТокен: {nft_token} Успешно добавлена'),
        Button(Const('📃В главное меню'), id='to_main_menu', on_click=switch_to_main_menu),
        getter=accept_nft_link,
        state=AllRequestsSG.accept
    )
)

dp.include_router(start_dialog)
dp.include_router(watch_all_requests_dialog)
setup_dialogs(dp)


async def on_startup(bot):
    run_param = False
    # if run_param:
    #     await drop_db()
    #
    # await create_db()


async def on_shutdown(bot):
    print('бот лег')


dp.startup.register(on_startup)
dp.shutdown.register(on_shutdown)

# dp.update.middleware(DataBaseSession(session_pool=session_maker))
dp.callback_query.middleware(CallbackAnswerMiddleware())

dp.run_polling(bot)
