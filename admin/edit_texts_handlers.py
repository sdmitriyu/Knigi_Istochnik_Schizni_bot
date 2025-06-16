from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from data.models import GalleryText, OrderPretext
from admin.state_book import GalleryTextState, OrderPretextState
from aiogram.fsm.context import FSMContext
from data.models import Admin # Для проверки админ-прав
from config.keyboards import texts_menu_kb # Добавил импорт texts_menu_kb
from typing import cast # Добавляем импорт cast

admin_texts_router = Router()

async def is_admin_filter(message: Message) -> bool:
    if not message.from_user:
        return False
    return Admin.get_or_none(Admin.user_id == message.from_user.id) is not None

admin_texts_router.message.filter(is_admin_filter)

# --- Обработчики для редактирования текста галереи ---
@admin_texts_router.message(F.text == "🖼 Изменить текст галереи")
async def show_gallery_text_for_edit(message: Message):
    gallery_text_obj = GalleryText.get_or_none()
    current_text = gallery_text_obj.text if gallery_text_obj else "*Текущий текст галереи отсутствует.*"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Изменить текст галереи", callback_data="edit_gallery_text_inline")]
    ])

    await message.answer(
        f"""*Текущий текст галереи:*
{current_text}""",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

@admin_texts_router.callback_query(F.data == "edit_gallery_text_inline")
async def edit_gallery_text_inline(callback_query: CallbackQuery, state: FSMContext):
    await state.set_state(GalleryTextState.text)
    if callback_query.message:
        message_obj = cast(Message, callback_query.message) # Явное приведение к типу Message
        await message_obj.answer("Введите новый текст для галереи:")
    await callback_query.answer()

@admin_texts_router.message(GalleryTextState.text)
async def process_gallery_text(message: Message, state: FSMContext):
    if not message.text or len(message.text.strip()) < 5:
        await message.answer("Текст для галереи должен содержать минимум 5 символов. Попробуйте еще раз:", reply_markup=texts_menu_kb)
        return
    
    try:
        gallery_text_obj = GalleryText.get_or_none()
        if gallery_text_obj:
            gallery_text_obj.text = message.text.strip()
            gallery_text_obj.save()
            status = "обновлен"
        else:
            GalleryText.create(text=message.text.strip())
            status = "создан"
        await message.answer(f"Текст для галереи успешно {status}!", reply_markup=texts_menu_kb)
    except Exception as e:
        await message.answer(f"Произошла ошибка при сохранении текста галереи: {str(e)}", reply_markup=texts_menu_kb)
    finally:
        await state.clear()

# --- Обработчики для редактирования текста заказа ---
@admin_texts_router.message(F.text == "📝 Изменить текст заказа")
async def show_order_pretext_for_edit(message: Message):
    order_pretext_obj = OrderPretext.get_or_none()
    current_text = order_pretext_obj.text if order_pretext_obj else "*Текущий текст перед заказом отсутствует.*"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Изменить текст заказа", callback_data="edit_order_pretext_inline")]
    ])

    await message.answer(
        f"""*Текущий текст перед заказом:*
{current_text}""",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

@admin_texts_router.callback_query(F.data == "edit_order_pretext_inline")
async def edit_order_pretext_inline(callback_query: CallbackQuery, state: FSMContext):
    await state.set_state(OrderPretextState.text)
    if callback_query.message:
        message_obj = cast(Message, callback_query.message) # Явное приведение к типу Message
        await message_obj.answer("Введите новый текст перед заказом:")
    await callback_query.answer()

@admin_texts_router.message(OrderPretextState.text)
async def process_order_pretext(message: Message, state: FSMContext):
    if not message.text or len(message.text.strip()) < 5:
        await message.answer("Текст перед заказом должен содержать минимум 5 символов. Попробуйте еще раз:", reply_markup=texts_menu_kb)
        return
    
    try:
        order_pretext_obj = OrderPretext.get_or_none()
        if order_pretext_obj:
            order_pretext_obj.text = message.text.strip()
            order_pretext_obj.save()
            status = "обновлен"
        else:
            OrderPretext.create(text=message.text.strip())
            status = "создан"
        await message.answer(f"Текст перед заказом успешно {status}!", reply_markup=texts_menu_kb)
    except Exception as e:
        await message.answer(f"Произошла ошибка при сохранении текста перед заказом: {str(e)}", reply_markup=texts_menu_kb)
    finally:
        await state.clear() 