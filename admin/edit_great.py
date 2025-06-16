from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from data.models import db, Greeting, Admin
from aiogram.fsm.context import FSMContext
from admin.state_book import GreetingTextState
from config.keyboards import texts_menu_kb
from typing import cast

admin_great_router = Router()

async def is_admin_filter(message: Message) -> bool:
    if not message.from_user:
        return False
    return Admin.get_or_none(Admin.user_id == message.from_user.id) is not None

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

@admin_great_router.callback_query(F.data == "edit_greeting_text_inline")
async def edit_greeting_text_inline(callback_query: CallbackQuery, state: FSMContext):
    await state.set_state(GreetingTextState.text)
    if callback_query.message:
        message_obj = cast(Message, callback_query.message)
        await message_obj.answer("Введите новый текст для приветствия:")
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

