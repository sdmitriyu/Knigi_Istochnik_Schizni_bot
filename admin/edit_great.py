from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from data.models import db, Greeting, Admin
from aiogram.fsm.context import FSMContext
from admin.state_book import GreetingTextState
from config.keyboards import texts_menu_kb
from typing import cast
from config.logger_config import setup_logger, log_debug, log_error, log_warning

admin_great_router = Router()
logger = setup_logger('admin_edit_great')

async def is_admin_filter(message: Message) -> bool:
    if not message.from_user:
        log_debug(logger, "is_admin_filter: Отсутствует информация о пользователе.", {})
        return False
    
    user_id = message.from_user.id
    is_admin = Admin.get_or_none(Admin.user_id == user_id) is not None
    log_debug(logger, f"is_admin_filter: Проверка пользователя {user_id}. Результат: {is_admin}", {"user_id": user_id, "is_admin": is_admin})
    return is_admin

admin_great_router.message.filter(is_admin_filter)

# Старый обработчик будет удален, вместо него будут FSM-обработчики
# @admin_router.message(F.text.startswith("Изменить приветствие"))
# async def edit_hello(message: Message):
#     try:
#         if not message.text:
#             await message.answer("Пожалуйста, укажите текст приветствия")
#             return
            
#         # Получаем текст после команды
#         new_text = message.text.replace("Изменить приветствие", "").strip()
#         if not new_text:
#             await message.answer("Пожалуйста, укажите текст приветствия после команды")
#             return
            
#         greeting = Greeting.get_or_none()
#         if greeting:
#             greeting.text = new_text
#             greeting.save()
#             status = "обновлено"
#         else:
#             greeting = Greeting.create(text=new_text)
#             status = "создано"
#         await message.answer(f"Приветствие успешно {status}!")
#     except Exception as e:
#         await message.answer(f"Произошла ошибка при сохранении приветствия: {str(e)}")

# Новый обработчик для кнопки "Изменить приветствие"
@admin_great_router.message(F.text == "👋 Изменить приветствие")
async def show_greeting_text_for_edit(message: Message):
    log_debug(logger, "Вход в show_greeting_text_for_edit", {"user_id": message.from_user.id if message.from_user else None})
    try:
        greeting_obj = Greeting.get_or_none()
        current_text = greeting_obj.text if greeting_obj else "*Текущий текст приветствия отсутствует.*"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Изменить приветствие", callback_data="edit_greeting_text_inline")]
        ])
        await message.answer(
            f"""*Текущий текст приветствия:*
{current_text}""",
            parse_mode="Markdown",
            reply_markup=keyboard
        )
    except Exception as e:
        log_error(logger, e, "Ошибка в show_greeting_text_for_edit")

@admin_great_router.callback_query(F.data == "edit_greeting_text_inline")
async def edit_greeting_text_inline(callback_query: CallbackQuery, state: FSMContext):
    log_debug(logger, f"Коллбэк получен: {callback_query.data}")
    await state.set_state(GreetingTextState.text)
    if callback_query.message:
        message_obj = cast(Message, callback_query.message)
        log_debug(logger, "Отправка запроса на ввод нового текста приветствия")
        await message_obj.answer("Введите новый текст для приветствия:")
    else:
        log_warning(logger, "callback_query.message is None in edit_greeting_text_inline", {})
    await callback_query.answer()

# Обработчик состояния для получения нового текста приветствия
@admin_great_router.message(GreetingTextState.text)
async def process_greeting_text(message: Message, state: FSMContext):
    if not message.text or len(message.text.strip()) < 5:
        await message.answer("Текст приветствия должен содержать минимум 5 символов. Попробуйте еще раз:", reply_markup=texts_menu_kb)
        return
    
    try:
        greeting_obj = Greeting.get_or_none()
        if greeting_obj:
            greeting_obj.text = message.text.strip()
            greeting_obj.save()
            status = "обновлен"
        else:
            Greeting.create(text=message.text.strip())
            status = "создан"
        await message.answer(f"Приветствие успешно {status}!", reply_markup=texts_menu_kb)
    except Exception as e:
        await message.answer(f"Произошла ошибка при сохранении приветствия: {str(e)}", reply_markup=texts_menu_kb)
    finally:
        await state.clear()

