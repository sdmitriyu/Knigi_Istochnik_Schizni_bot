import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from aiogram.types import Message, Contact, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from data.models import db
from data.models import Admin
from aiogram import Router, F
from config.keyboards import admins_menu_kb
from aiogram.fsm.context import FSMContext
from admin.state_book import AdminEditState
from typing import cast

register_admin_router = Router()

async def is_admin_filter(message: Message) -> bool:
    if not message.from_user:
        return False
    return Admin.get_or_none(Admin.user_id == message.from_user.id) is not None

# register_admin_router.message.filter(is_admin_filter) # Временно закомментировано для отладки

@register_admin_router.message(F.text == "➕ Добавить администратора")
async def add_admin_start(message: Message):
    await message.answer(
        "Пожалуйста, отправьте контакт пользователя, которого хотите добавить в администраторы.\n"
        "Для этого нажмите на кнопку 'Поделиться контактом' в меню ввода сообщения.",
        reply_markup=admins_menu_kb
    )

@register_admin_router.message(F.contact)
async def add_admin_contact(message: Message):
    try:
        contact = message.contact
        if contact is None:
            await message.answer("Не удалось получить контактные данные.", reply_markup=admins_menu_kb)
            return
        
        # Добавляем отладочный вывод
        print(f"DEBUG: Received contact.user_id: {contact.user_id}")
        print(f"DEBUG: Received contact.first_name: {contact.first_name}")
        print(f"DEBUG: Received contact.phone_number: {contact.phone_number}")

        # Создаем или обновляем администратора
        admin, created = Admin.get_or_create(user_id=contact.user_id)
        admin.user_name = contact.first_name + (f" {contact.last_name}" if contact.last_name else "")
        # Изменено: сохраняем phone_number как строку без преобразования в int
        admin.phone = contact.phone_number if contact.phone_number else "" 
        admin.save()
        status = "обновлен" if not created else "добавлен"
        await message.answer(f"Администратор успешно {status}!", reply_markup=admins_menu_kb)
    except Exception as e:
        await message.answer(f"Произошла ошибка при добавлении администратора: {str(e)}", reply_markup=admins_menu_kb)

async def list_admins(message: Message):
    admins = Admin.select()  # Получаем всех администраторов из базы
    print(f"DEBUG: Admins retrieved from DB: {[(admin.user_id, admin.user_name, admin.phone) for admin in admins]}") # Отладочный вывод
    if not admins:
        await message.answer("Список администраторов пуст", reply_markup=admins_menu_kb)
        return
    
    await message.answer("Список администраторов:") # Отправляем заголовок один раз
    for admin in admins:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Изменить администратора", callback_data=f"edit_admin_{admin.user_id}"),
             InlineKeyboardButton(text="🗑️ Удалить администратора", callback_data=f"delete_admin_{admin.user_id}")]
        ])
        await message.answer(
            f"ID: `{admin.user_id}`\n" # Используем обратные кавычки для моноширинного текста ID
            f"Имя: *{admin.user_name}*\n"
            f"Телефон: `{admin.phone}`", # Используем обратные кавычки для моноширинного текста телефона
            parse_mode="Markdown",
            reply_markup=keyboard
        )
    await message.answer("Выберите действие:", reply_markup=admins_menu_kb)

@register_admin_router.message(F.text == "🗑 Удалить администратора")
async def delete_admin(message: Message):
    admins = Admin.select()
    if not admins:
        await message.answer("Список администраторов пуст", reply_markup=admins_menu_kb)
        return
    
    response = "Выберите ID администратора для удаления:\n\n"
    for admin in admins:
        response += f"ID: {admin.user_id} - {admin.user_name}\n"
    await message.answer(response, reply_markup=admins_menu_kb)

@register_admin_router.message(lambda message: message.text is not None and message.text.isdigit() and Admin.get_or_none(Admin.user_id == int(message.text)))
async def delete_admin_by_id(message: Message):
    try:
        if message.text is None: return # Удовлетворяем линтер
        user_id = int(message.text) # message.text гарантированно не None благодаря лямбде
        admin = Admin.get(Admin.user_id == user_id)
        admin.delete_instance()
        await message.answer("Администратор успешно удален!", reply_markup=admins_menu_kb)
    except Exception as e:
        await message.answer(f"Произошла ошибка при удалении администратора: {str(e)}", reply_markup=admins_menu_kb)

@register_admin_router.message(F.text == "Обновить администратора")
async def update_admin_start(message: Message):
    admins = Admin.select()
    if not admins:
        await message.answer("Список администраторов пуст", reply_markup=admins_menu_kb)
        return
    
    response = "Выберите ID администратора для обновления:\n\n"
    for admin in admins:
        response += f"ID: {admin.user_id} - {admin.user_name}\n"
    await message.answer(response, reply_markup=admins_menu_kb)

@register_admin_router.message(lambda message: message.text is not None and message.text.isdigit() and Admin.get_or_none(Admin.user_id == int(message.text)))
async def update_admin_contact(message: Message):
    try:
        if message.text is None: return # Удовлетворяем линтер
        user_id = int(message.text) # message.text гарантированно не None благодаря лямбде
        admin = Admin.get_or_none(Admin.user_id == user_id)
        if not admin:
            await message.answer("Администратор не найден!", reply_markup=admins_menu_kb)
            return
        await message.answer(
            f"Отправьте новый контакт для обновления данных администратора {admin.user_name}.\n"
            "Для этого нажмите на кнопку 'Поделиться контактом' в меню ввода сообщения.",
            reply_markup=admins_menu_kb
        )
    except Exception as e:
        await message.answer(f"Произошла ошибка при обновлении данных администратора: {str(e)}", reply_markup=admins_menu_kb)

@register_admin_router.message(F.contact)
async def update_admin_by_contact(message: Message):
    try:
        contact = message.contact
        if contact is None:
            await message.answer("Не удалось получить контактные данные.", reply_markup=admins_menu_kb)
            return
        # Создаем или обновляем администратора
        admin, created = Admin.get_or_create(user_id=contact.user_id)
        admin.user_name = contact.first_name + (f" {contact.last_name}" if contact.last_name else "")
        admin.phone = int(contact.phone_number.replace("+", ""))
        admin.save()
        status = "обновлены" if not created else "добавлены"
        await message.answer(f"Данные администратора успешно {status}!", reply_markup=admins_menu_kb)
    except Exception as e:
        await message.answer(f"Произошла ошибка при обновлении данных администратора: {str(e)}", reply_markup=admins_menu_kb)

@register_admin_router.message(F.text == "👥 Список администраторов")
async def show_list_admins(message: Message):
    user_id = message.from_user.id if message.from_user else "Unknown"
    print(f"DEBUG: show_list_admins called for user ID: {user_id}")
    await list_admins(message)

# Обработчики для редактирования администраторов
@register_admin_router.callback_query(F.data.regexp(r"^edit_admin_\d+$"))
async def edit_admin_callback_handler(callback_query: CallbackQuery, state: FSMContext):
    if not callback_query.data:
        await callback_query.answer("❌ Ошибка данных коллбэка.", show_alert=True)
        return

    print(f"DEBUG: callback_query.data: {callback_query.data}") # Добавлено для отладки
    admin_user_id = int(callback_query.data.split("_")[2])
    print(f"DEBUG: Extracted admin_user_id: {admin_user_id}") # Добавлено для отладки
    admin = Admin.get_or_none(Admin.user_id == admin_user_id)
    print(f"DEBUG: Admin found: {admin is not None}") # Добавлено для отладки

    if not admin:
        await callback_query.answer("❌ Администратор не найден.", show_alert=True)
        return

    await state.update_data(user_id=admin_user_id)
    await state.set_state(AdminEditState.edit_field)

    edit_options_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Изменить имя", callback_data=f"edit_admin_field_user_name")],
        [InlineKeyboardButton(text="Изменить телефон", callback_data=f"edit_admin_field_phone")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data=f"cancel_edit_admin")]
    ])

    if callback_query.message:
        message_obj = cast(Message, callback_query.message)
        await message_obj.answer(
            f"✏️ Выбран администратор: *{admin.user_name}* (ID: `{admin.user_id}`)\n\n"
            "Выберите поле для редактирования:",
            parse_mode="Markdown",
            reply_markup=edit_options_keyboard
        )
    else:
        await callback_query.answer("Выберите поле для редактирования:", show_alert=True)

    await callback_query.answer()

@register_admin_router.callback_query(F.data == "cancel_edit_admin")
async def cancel_edit_admin_callback_handler(callback_query: CallbackQuery, state: FSMContext):
    await state.clear()
    if callback_query.message:
        message_obj = cast(Message, callback_query.message)
        await message_obj.edit_text("❌ Редактирование администратора отменено.")
    await callback_query.answer("Редактирование администратора отменено.")

# Обработчики для удаления администраторов
@register_admin_router.callback_query(F.data.startswith("delete_admin_"))
async def delete_admin_callback_handler(callback_query: CallbackQuery):
    if not callback_query.data:
        await callback_query.answer("❌ Ошибка данных коллбэка.", show_alert=True)
        return

    admin_user_id = int(callback_query.data.split("_")[2])
    admin = Admin.get_or_none(Admin.user_id == admin_user_id)

    if not admin:
        await callback_query.answer("❌ Администратор не найден.", show_alert=True)
        return

    confirm_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"confirm_delete_admin_{admin.user_id}"),
         InlineKeyboardButton(text="❌ Нет, отмена", callback_data=f"cancel_delete_admin")]
    ])

    if callback_query.message:
        message_obj = cast(Message, callback_query.message)
        await message_obj.answer(
            f"🗑️ Вы действительно хотите удалить администратора *{admin.user_name}* (ID: `{admin.user_id}`)?",
            parse_mode="Markdown",
            reply_markup=confirm_keyboard
        )
    else:
        await callback_query.answer("Подтвердите удаление администратора.", show_alert=True)
    
    await callback_query.answer()

@register_admin_router.callback_query(F.data.startswith("confirm_delete_admin_"))
async def confirm_delete_admin_callback_handler(callback_query: CallbackQuery):
    if not callback_query.data:
        await callback_query.answer("❌ Ошибка данных коллбэка.", show_alert=True)
        return

    admin_user_id = int(callback_query.data.split("_")[3])

    try:
        admin = Admin.get_or_none(Admin.user_id == admin_user_id)
        if not admin:
            await callback_query.answer("❌ Администратор не найден.", show_alert=True)
            return
        
        admin_name = admin.user_name
        admin.delete_instance()
        
        if callback_query.message:
            message_obj = cast(Message, callback_query.message)
            await message_obj.edit_text(f"✅ Администратор *{admin_name}* успешно удален.", parse_mode="Markdown")
        await callback_query.answer(f"✅ Администратор {admin_name} успешно удален.")

    except Exception as e:
        print(f"DEBUG: Error in confirm_delete_admin_callback_handler: {e}")
        await callback_query.answer(f"❌ Произошла ошибка при удалении администратора: {str(e)}", show_alert=True)

@register_admin_router.callback_query(F.data == "cancel_delete_admin")
async def cancel_delete_admin_callback_handler(callback_query: CallbackQuery):
    if callback_query.message:
        message_obj = cast(Message, callback_query.message)
        await message_obj.edit_text("❌ Удаление администратора отменено.")
    await callback_query.answer("Удаление администратора отменено.")

# Обработчики для обновления данных администратора
@register_admin_router.callback_query(AdminEditState.edit_field, F.data.startswith("edit_admin_field_"))
async def choose_admin_edit_field_callback_handler(callback_query: CallbackQuery, state: FSMContext):
    print(f"DEBUG: choose_admin_edit_field_callback_handler called. callback_query.data: {callback_query.data}")

    if not callback_query.data:
        await callback_query.answer("❌ Ошибка данных коллбэка.", show_alert=True)
        return

    field_to_edit = callback_query.data.split("_")[3]
    print(f"DEBUG: field_to_edit: {field_to_edit}")

    current_data = await state.get_data()
    admin_user_id = current_data.get("user_id")

    if not admin_user_id:
        await callback_query.answer("❌ ID администратора для редактирования не найден.", show_alert=True)
        print("DEBUG: admin_user_id not found in state.")
        return

    admin = Admin.get_or_none(Admin.user_id == admin_user_id)
    if not admin:
        await callback_query.answer("❌ Администратор не найден.", show_alert=True)
        await state.clear()
        print("DEBUG: Admin not found in DB.")
        return

    if not callback_query.message:
        await callback_query.answer("❌ Не удалось получить информацию о сообщении.", show_alert=True)
        print("DEBUG: callback_query.message is None.")
        return
    
    message_obj = cast(Message, callback_query.message)

    # Установка соответствующего состояния FSM и запрос нового значения
    if field_to_edit == "user_name":
        await state.set_state(AdminEditState.new_user_name)
        await message_obj.answer(f"Введите новое имя пользователя для администратора *{admin.user_name}*:", parse_mode="Markdown")
        print(f"DEBUG: State set to new_user_name for {admin.user_name}")
    elif field_to_edit == "phone":
        await state.set_state(AdminEditState.new_phone)
        await message_obj.answer(f"Введите новый номер телефона для администратора *{admin.user_name}* (только цифры):", parse_mode="Markdown")
        print(f"DEBUG: State set to new_phone for {admin.user_name}")
    else:
        await callback_query.answer("❌ Неизвестное поле для редактирования.", show_alert=True)
        print(f"DEBUG: Unknown field to edit: {field_to_edit}")
        return

    await callback_query.answer()

@register_admin_router.message(AdminEditState.new_user_name)
async def process_new_admin_user_name(message: Message, state: FSMContext):
    if not message.text or len(message.text.strip()) < 2:
        await message.answer("❌ Имя пользователя должно содержать минимум 2 символа. Попробуйте еще раз:")
        return
    
    data = await state.get_data()
    admin_user_id = data.get("user_id")
    admin = Admin.get_or_none(Admin.user_id == admin_user_id)

    if not admin:
        await message.answer("❌ Администратор не найден. Пожалуйста, начните редактирование заново.")
        await state.clear()
        return

    try:
        admin.user_name = message.text.strip()
        admin.save()
        await message.answer(f"✅ Имя пользователя администратора *{admin.user_name}* успешно обновлено!", parse_mode="Markdown")
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка при обновлении имени пользователя: {str(e)}")
    finally:
        await state.clear()

@register_admin_router.message(AdminEditState.new_phone)
async def process_new_admin_phone(message: Message, state: FSMContext):
    if not message.text: # Проверяем, что текст не пустой
        await message.answer("❌ Номер телефона не может быть пустым. Попробуйте еще раз:")
        return
    
    # Удаляем проверку на isdigit() и преобразование в int
    new_phone_number = message.text.strip()

    data = await state.get_data()
    admin_user_id = data.get("user_id")
    admin = Admin.get_or_none(Admin.user_id == admin_user_id)

    if not admin:
        await message.answer("❌ Администратор не найден. Пожалуйста, начните редактирование заново.")
        await state.clear()
        return

    try:
        admin.phone = new_phone_number
        admin.save()
        await message.answer(f"✅ Телефон администратора *{admin.user_name}* успешно обновлен!", parse_mode="Markdown")
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка при обновлении телефона: {str(e)}")
    finally:
        await state.clear()

