import sys
import os
from config.logger_config import setup_logger, log_debug, log_error, log_info, log_warning

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
logger = setup_logger('admin_rigister_admin')

async def is_admin_filter(message: Message) -> bool:
    if not message.from_user:
        log_debug(logger, "is_admin_filter: Отсутствует информация о пользователе.", {})
        return False
    
    user_id = message.from_user.id
    is_admin = Admin.get_or_none(Admin.user_id == user_id) is not None
    log_debug(logger, f"is_admin_filter: Проверка пользователя {user_id}. Результат: {is_admin}", {"user_id": user_id, "is_admin": is_admin})
    return is_admin

register_admin_router.message.filter(is_admin_filter) # Раскомментировано

@register_admin_router.message(F.text == "➕ Добавить администратора")
async def add_admin_start(message: Message):
    log_debug(logger, "Вход в add_admin_start", {"user_id": message.from_user.id if message.from_user else None})
    try:
        await message.answer(
            "Пожалуйста, отправьте контакт пользователя, которого хотите добавить в администраторы.\n"
            "Для этого нажмите на кнопку 'Поделиться контактом' в меню ввода сообщения.",
            reply_markup=admins_menu_kb
        )
    except Exception as e:
        log_error(logger, e, "Ошибка в add_admin_start")

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
        log_error(logger, e, "Ошибка в add_admin_contact")

async def list_admins(message: Message):
    log_debug(logger, "Начало функции list_admins")
    admins = Admin.select()  # Получаем всех администраторов из базы
    if not admins:
        log_info(logger, "Список администраторов пуст")
        await message.answer("Список администраторов пуст", reply_markup=admins_menu_kb)
        return
    
    log_info(logger, f"Найдено {len(admins)} администраторов. Отправка списка.")
    await message.answer("Список администраторов:") # Отправляем заголовок один раз
    for admin in admins:
        log_debug(logger, f"Отправка информации об администраторе: {admin.user_id}", {"admin_id": admin.user_id, "user_name": admin.user_name})
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
    log_debug(logger, "Список администраторов отправлен. Завершение list_admins")
    await message.answer("Выберите действие:", reply_markup=admins_menu_kb)

@register_admin_router.message(F.text == "👥 Список администраторов")
async def show_list_admins(message: Message):
    user_id = message.from_user.id if message.from_user else "Unknown"
    log_debug(logger, "Вход в show_list_admins", {"user_id": user_id})
    await list_admins(message)
    log_debug(logger, "Выход из show_list_admins", {"user_id": user_id})

# Обработчики для редактирования администраторов
@register_admin_router.callback_query(F.data.regexp(r"^edit_admin_\\d+$"))
async def edit_admin_callback_handler(callback_query: CallbackQuery, state: FSMContext):
    log_debug(logger, "Вход в edit_admin_callback_handler", {"user_id": callback_query.from_user.id if callback_query.from_user else None, "callback_data": callback_query.data})
    if not callback_query.data:
        log_warning(logger, "Отсутствуют данные коллбэка в edit_admin_callback_handler", {"user_id": callback_query.from_user.id if callback_query.from_user else None})
        await callback_query.answer("❌ Ошибка данных коллбэка.", show_alert=True)
        return

    try:
        admin_user_id = int(callback_query.data.split("_")[2])
        log_debug(logger, f"Извлечен admin_user_id: {admin_user_id}")
    except (ValueError, IndexError) as e:
        log_error(logger, e, f"Неверный формат callback_data для edit_admin: {callback_query.data}")
        await callback_query.answer("❌ Неверный формат данных администратора.", show_alert=True)
        return

    admin = Admin.get_or_none(Admin.user_id == admin_user_id)

    if not admin:
        log_warning(logger, "Администратор не найден для редактирования", {"admin_user_id": admin_user_id})
        await callback_query.answer("❌ Администратор не найден.", show_alert=True)
        return

    await state.update_data(user_id=admin_user_id) # Store admin_user_id in FSM
    await state.set_state(AdminEditState.edit_field)
    log_info(logger, "Состояние FSM установлено на AdminEditState.edit_field", {"admin_user_id": admin_user_id, "user_id": callback_query.from_user.id if callback_query.from_user else None})

    edit_options_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Изменить имя", callback_data=f"edit_admin_field_user_name")],
        [InlineKeyboardButton(text="Изменить телефон", callback_data=f"edit_admin_field_phone")],
        [InlineKeyboardButton(text="Изменить роль", callback_data=f"edit_admin_field_role")],
        [InlineKeyboardButton(text="Изменить отображаемое имя", callback_data=f"edit_admin_field_display_name")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data=f"cancel_edit_admin")]
    ])

    if callback_query.message:
        message_obj = cast(Message, callback_query.message)
        log_debug(logger, "Отправка клавиатуры выбора поля для редактирования администратора")
        await message_obj.answer(
            f"✏️ Выбран администратор: *{admin.user_name}* (ID: `{admin.user_id}`)\n\n"
            "Выберите поле для редактирования:",
            parse_mode="Markdown",
            reply_markup=edit_options_keyboard
        )
    else:
        log_warning(logger, "callback_query.message is None в edit_admin_callback_handler")
        await callback_query.answer("Выберите поле для редактирования:", show_alert=True)

    await callback_query.answer()
    log_debug(logger, "Выход из edit_admin_callback_handler")

@register_admin_router.callback_query(F.data == "cancel_edit_admin")
async def cancel_edit_admin_callback_handler(callback_query: CallbackQuery, state: FSMContext):
    log_debug(logger, "Вход в cancel_edit_admin_callback_handler", {"user_id": callback_query.from_user.id if callback_query.from_user else None})
    await state.clear()
    if callback_query.message:
        message_obj = cast(Message, callback_query.message)
        await message_obj.edit_text("❌ Редактирование администратора отменено.")
    await callback_query.answer("Редактирование администратора отменено.")
    log_debug(logger, "Выход из cancel_edit_admin_callback_handler")

# Обработчики для удаления администраторов
@register_admin_router.callback_query(F.data.startswith("delete_admin_"))
async def delete_admin_callback_handler(callback_query: CallbackQuery):
    log_debug(logger, "Вход в delete_admin_callback_handler", {"user_id": callback_query.from_user.id if callback_query.from_user else None, "callback_data": callback_query.data})
    if not callback_query.data:
        log_warning(logger, "Отсутствуют данные коллбэка в delete_admin_callback_handler", {"user_id": callback_query.from_user.id if callback_query.from_user else None})
        await callback_query.answer("❌ Ошибка данных коллбэка.", show_alert=True)
        return

    try:
        admin_user_id = int(callback_query.data.split("_")[2])
        log_debug(logger, f"Извлечен admin_user_id для удаления: {admin_user_id}")
    except (ValueError, IndexError) as e:
        log_error(logger, e, f"Неверный формат callback_data для delete_admin: {callback_query.data}")
        await callback_query.answer("❌ Неверный формат данных администратора.", show_alert=True)
        return

    admin = Admin.get_or_none(Admin.user_id == admin_user_id)

    if not admin:
        log_warning(logger, "Администратор не найден для удаления", {"admin_user_id": admin_user_id})
        await callback_query.answer("❌ Администратор не найден.", show_alert=True)
        return

    confirm_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"confirm_delete_admin_{admin.user_id}"),
         InlineKeyboardButton(text="❌ Нет, отмена", callback_data=f"cancel_delete_admin")]
    ])

    if callback_query.message:
        message_obj = cast(Message, callback_query.message)
        log_debug(logger, "Отправка запроса на подтверждение удаления администратора")
        await message_obj.answer(
            f"🗑️ Вы действительно хотите удалить администратора *{admin.user_name}* (ID: `{admin.user_id}`)?",
            parse_mode="Markdown",
            reply_markup=confirm_keyboard
        )
    else:
        log_warning(logger, "callback_query.message is None в delete_admin_callback_handler")
        await callback_query.answer("Подтвердите удаление администратора.", show_alert=True)
    
    await callback_query.answer()
    log_debug(logger, "Выход из delete_admin_callback_handler")

@register_admin_router.callback_query(F.data.startswith("confirm_delete_admin_"))
async def confirm_delete_admin_callback_handler(callback_query: CallbackQuery):
    log_debug(logger, "Вход в confirm_delete_admin_callback_handler", {"user_id": callback_query.from_user.id if callback_query.from_user else None, "callback_data": callback_query.data})
    if not callback_query.data:
        log_warning(logger, "Отсутствуют данные коллбэка в confirm_delete_admin_callback_handler", {"user_id": callback_query.from_user.id if callback_query.from_user else None})
        await callback_query.answer("❌ Ошибка данных коллбэка.", show_alert=True)
        return

    try:
        admin_user_id = int(callback_query.data.split("_")[3])
        log_debug(logger, f"Извлечен admin_user_id для подтверждения удаления: {admin_user_id}")
    except (ValueError, IndexError) as e:
        log_error(logger, e, f"Неверный формат callback_data для confirm_delete_admin: {callback_query.data}")
        await callback_query.answer("❌ Неверный формат данных администратора.", show_alert=True)
        return

    try:
        admin = Admin.get_or_none(Admin.user_id == admin_user_id)
        if not admin:
            log_warning(logger, "Администратор не найден для подтверждения удаления", {"admin_user_id": admin_user_id})
            await callback_query.answer("❌ Администратор не найден.", show_alert=True)
            return
        
        admin_name = admin.user_name
        admin.delete_instance()
        log_info(logger, "Администратор успешно удален", {"admin_user_id": admin_user_id, "admin_name": admin_name})
        
        if callback_query.message:
            message_obj = cast(Message, callback_query.message)
            log_debug(logger, "Обновление сообщения после удаления администратора")
            await message_obj.edit_text(f"✅ Администратор *{admin_name}* успешно удален.", parse_mode="Markdown")
        await callback_query.answer(f"✅ Администратор {admin_name} успешно удален.")

    except Exception as e:
        log_error(logger, e, "Ошибка в confirm_delete_admin_callback_handler")
        await callback_query.answer(f"❌ Произошла ошибка при удалении администратора: {str(e)}", show_alert=True)
    log_debug(logger, "Выход из confirm_delete_admin_callback_handler")

@register_admin_router.callback_query(F.data == "cancel_delete_admin")
async def cancel_delete_admin_callback_handler(callback_query: CallbackQuery):
    log_debug(logger, "Вход в cancel_delete_admin_callback_handler", {"user_id": callback_query.from_user.id if callback_query.from_user else None})
    if callback_query.message:
        message_obj = cast(Message, callback_query.message)
        await message_obj.edit_text("❌ Удаление администратора отменено.")
    await callback_query.answer("Редактирование администратора отменено.")
    log_debug(logger, "Выход из cancel_delete_admin_callback_handler")

# Обработчики для обновления данных администратора
@register_admin_router.callback_query(AdminEditState.edit_field, F.data.startswith("edit_admin_field_"))
async def choose_admin_edit_field_callback_handler(callback_query: CallbackQuery, state: FSMContext):
    log_debug(logger, "Вход в choose_admin_edit_field_callback_handler", {"user_id": callback_query.from_user.id if callback_query.from_user else None, "callback_data": callback_query.data})
    if not callback_query.data:
        log_warning(logger, "Отсутствуют данные коллбэка в choose_admin_edit_field_callback_handler", {"user_id": callback_query.from_user.id if callback_query.from_user else None})
        await callback_query.answer("❌ Ошибка данных коллбэка.", show_alert=True)
        return

    field_to_edit = callback_query.data.split("_")[3]
    log_debug(logger, f"Поле для редактирования: {field_to_edit}")

    current_data = await state.get_data()
    admin_user_id = current_data.get("user_id")
    log_debug(logger, f"admin_user_id из состояния: {admin_user_id}")

    if not admin_user_id:
        log_error(logger, ValueError("ID администратора для редактирования не найден в состоянии."), "admin_user_id is None in state")
        await callback_query.answer("❌ ID администратора для редактирования не найден.", show_alert=True)
        return

    admin = Admin.get_or_none(Admin.user_id == admin_user_id)
    if not admin:
        log_warning(logger, "Администратор не найден в базе данных для редактирования", {"admin_user_id": admin_user_id})
        await callback_query.answer("❌ Администратор не найден.", show_alert=True)
        await state.clear()
        return

    if not callback_query.message:
        log_warning(logger, "callback_query.message is None в choose_admin_edit_field_callback_handler")
        await callback_query.answer("❌ Не удалось получить информацию о сообщении.", show_alert=True)
        return
    
    message_obj = cast(Message, callback_query.message)

    # Установка соответствующего состояния FSM и запрос нового значения
    if field_to_edit == "user_name":
        await state.set_state(AdminEditState.new_user_name)
        log_info(logger, "Установка состояния new_user_name", {"admin_user_id": admin_user_id})
        await message_obj.answer(f"Введите новое имя пользователя для администратора *{admin.user_name}*:", parse_mode="Markdown")
    elif field_to_edit == "phone":
        await state.set_state(AdminEditState.new_phone)
        log_info(logger, "Установка состояния new_phone", {"admin_user_id": admin_user_id})
        await message_obj.answer(f"Введите новый номер телефона для администратора *{admin.user_name}* (только цифры):", parse_mode="Markdown")
    elif field_to_edit == "role":
        await state.set_state(AdminEditState.new_role)
        log_info(logger, "Установка состояния new_role", {"admin_user_id": admin_user_id})
        await message_obj.answer(f"Введите новую роль для администратора *{admin.user_name}* (например, 'admin', 'manager', 'tech_support'):", parse_mode="Markdown")
    elif field_to_edit == "display_name":
        await state.set_state(AdminEditState.new_display_name)
        log_info(logger, "Установка состояния new_display_name", {"admin_user_id": admin_user_id})
        await message_obj.answer(f"Введите новое отображаемое имя для администратора *{admin.user_name}* (например, 'Иван (Менеджер)'):", parse_mode="Markdown")
    else:
        log_warning(logger, f"Неизвестное поле для редактирования: {field_to_edit}", {"field": field_to_edit, "user_id": callback_query.from_user.id if callback_query.from_user else None})
        await callback_query.answer("❌ Неизвестное поле для редактирования.", show_alert=True)
        return

    await callback_query.answer()
    log_debug(logger, "Выход из choose_admin_edit_field_callback_handler")

@register_admin_router.message(AdminEditState.new_user_name)
async def process_new_admin_user_name(message: Message, state: FSMContext):
    log_debug(logger, "Вход в process_new_admin_user_name", {"user_id": message.from_user.id if message.from_user else None, "message_text": message.text[:50] if message.text else ""})
    if not message.text or len(message.text.strip()) < 2:
        log_warning(logger, "Новое имя пользователя слишком короткое", {"user_id": message.from_user.id if message.from_user else None, "text_len": len(message.text.strip()) if message.text else 0})
        await message.answer("❌ Имя пользователя должно содержать минимум 2 символа. Попробуйте еще раз:", parse_mode="Markdown")
        return
    
    current_data = await state.get_data()
    admin_user_id = current_data.get("user_id")
    
    if not admin_user_id:
        log_error(logger, ValueError("ID администратора не найден в состоянии для обновления имени пользователя."), "admin_user_id is None in state for user_name update")
        await message.answer("Произошла ошибка при обновлении имени пользователя. Пожалуйста, попробуйте еще раз.")
        await state.clear()
        return
    
    try:
        admin = Admin.get_or_none(Admin.user_id == admin_user_id)
        if admin:
            old_name = admin.user_name
            admin.user_name = message.text.strip()
            admin.save()
            log_info(logger, "Имя администратора обновлено", {"admin_user_id": admin_user_id, "old_name": old_name, "new_name": admin.user_name})
            await message.answer(f"✅ Имя пользователя для *{old_name}* успешно обновлено на *{admin.user_name}*!", parse_mode="Markdown", reply_markup=admins_menu_kb)
        else:
            log_warning(logger, "Администратор не найден для обновления имени пользователя", {"admin_user_id": admin_user_id})
            await message.answer("❌ Администратор не найден. Пожалуйста, попробуйте еще раз.", reply_markup=admins_menu_kb)
    except Exception as e:
        log_error(logger, e, "Ошибка при обновлении имени пользователя администратора")
        await message.answer(f"❌ Произошла ошибка при обновлении имени пользователя: {str(e)}", reply_markup=admins_menu_kb)
    finally:
        await state.clear()
    log_debug(logger, "Выход из process_new_admin_user_name")

@register_admin_router.message(AdminEditState.new_phone)
async def process_new_admin_phone(message: Message, state: FSMContext):
    log_debug(logger, "Вход в process_new_admin_phone", {"user_id": message.from_user.id if message.from_user else None, "message_text": message.text[:50] if message.text else ""})
    if not message.text or not message.text.strip().isdigit() or len(message.text.strip()) < 5:
        log_warning(logger, "Новый номер телефона некорректен", {"user_id": message.from_user.id if message.from_user else None, "phone_text": message.text[:50] if message.text else ""})
        await message.answer("❌ Номер телефона должен содержать только цифры и быть не менее 5 символов. Попробуйте еще раз:", parse_mode="Markdown")
        return
    
    current_data = await state.get_data()
    admin_user_id = current_data.get("user_id")

    if not admin_user_id:
        log_error(logger, ValueError("ID администратора не найден в состоянии для обновления телефона."), "admin_user_id is None in state for phone update")
        await message.answer("Произошла ошибка при обновлении телефона. Пожалуйста, попробуйте еще раз.")
        await state.clear()
        return
    
    try:
        admin = Admin.get_or_none(Admin.user_id == admin_user_id)
        if admin:
            old_phone = admin.phone
            admin.phone = message.text.strip()
            admin.save()
            log_info(logger, "Телефон администратора обновлен", {"admin_user_id": admin_user_id, "old_phone": old_phone, "new_phone": admin.phone})
            await message.answer(f"✅ Телефон для *{admin.user_name}* успешно обновлен на *{admin.phone}*!", parse_mode="Markdown", reply_markup=admins_menu_kb)
        else:
            log_warning(logger, "Администратор не найден для обновления телефона", {"admin_user_id": admin_user_id})
            await message.answer("❌ Администратор не найден. Пожалуйста, попробуйте еще раз.", reply_markup=admins_menu_kb)
    except Exception as e:
        log_error(logger, e, "Ошибка при обновлении телефона администратора")
        await message.answer(f"❌ Произошла ошибка при обновлении телефона: {str(e)}", reply_markup=admins_menu_kb)
    finally:
        await state.clear()
    log_debug(logger, "Выход из process_new_admin_phone")

@register_admin_router.message(AdminEditState.new_role)
async def process_new_admin_role(message: Message, state: FSMContext):
    log_debug(logger, "Вход в process_new_admin_role", {"user_id": message.from_user.id if message.from_user else None, "message_text": message.text[:50] if message.text else ""})
    if not message.text or len(message.text.strip()) < 2:
        log_warning(logger, "Новая роль слишком короткая", {"user_id": message.from_user.id if message.from_user else None, "text_len": len(message.text.strip()) if message.text else 0})
        await message.answer("❌ Роль должна содержать минимум 2 символа. Попробуйте еще раз:", parse_mode="Markdown")
        return

    current_data = await state.get_data()
    admin_user_id = current_data.get("user_id")

    if not admin_user_id:
        log_error(logger, ValueError("ID администратора не найден в состоянии для обновления роли."), "admin_user_id is None in state for role update")
        await message.answer("Произошла ошибка при обновлении роли. Пожалуйста, попробуйте еще раз.")
        await state.clear()
        return

    try:
        admin = Admin.get_or_none(Admin.user_id == admin_user_id)
        if admin:
            old_role = admin.role
            admin.role = message.text.strip()
            admin.save()
            log_info(logger, "Роль администратора обновлена", {"admin_user_id": admin_user_id, "old_role": old_role, "new_role": admin.role})
            await message.answer(f"✅ Роль для *{admin.user_name}* успешно обновлена на *{admin.role}*!", parse_mode="Markdown", reply_markup=admins_menu_kb)
        else:
            log_warning(logger, "Администратор не найден для обновления роли", {"admin_user_id": admin_user_id})
            await message.answer("❌ Администратор не найден. Пожалуйста, попробуйте еще раз.", reply_markup=admins_menu_kb)
    except Exception as e:
        log_error(logger, e, "Ошибка при обновлении роли администратора")
        await message.answer(f"❌ Произошла ошибка при обновлении роли: {str(e)}", reply_markup=admins_menu_kb)
    finally:
        await state.clear()
    log_debug(logger, "Выход из process_new_admin_role")

@register_admin_router.message(AdminEditState.new_display_name)
async def process_new_admin_display_name(message: Message, state: FSMContext):
    log_debug(logger, "Вход в process_new_admin_display_name", {"user_id": message.from_user.id if message.from_user else None, "message_text": message.text[:50] if message.text else ""})
    if not message.text or len(message.text.strip()) < 2:
        log_warning(logger, "Новое отображаемое имя слишком короткое", {"user_id": message.from_user.id if message.from_user else None, "text_len": len(message.text.strip()) if message.text else 0})
        await message.answer("❌ Отображаемое имя должно содержать минимум 2 символа. Попробуйте еще раз:", parse_mode="Markdown")
        return

    current_data = await state.get_data()
    admin_user_id = current_data.get("user_id")

    if not admin_user_id:
        log_error(logger, ValueError("ID администратора не найден в состоянии для обновления отображаемого имени."), "admin_user_id is None in state for display_name update")
        await message.answer("Произошла ошибка при обновлении отображаемого имени. Пожалуйста, попробуйте еще раз.")
        await state.clear()
        return

    try:
        admin = Admin.get_or_none(Admin.user_id == admin_user_id)
        if admin:
            old_display_name = admin.display_name
            admin.display_name = message.text.strip()
            admin.save()
            log_info(logger, "Отображаемое имя администратора обновлено", {"admin_user_id": admin_user_id, "old_display_name": old_display_name, "new_display_name": admin.display_name})
            await message.answer(f"✅ Отображаемое имя для *{admin.user_name}* успешно обновлено на *{admin.display_name}*!", parse_mode="Markdown", reply_markup=admins_menu_kb)
        else:
            log_warning(logger, "Администратор не найден для обновления отображаемого имени", {"admin_user_id": admin_user_id})
            await message.answer("❌ Администратор не найден. Пожалуйста, попробуйте еще раз.", reply_markup=admins_menu_kb)
    except Exception as e:
        log_error(logger, e, "Ошибка при обновлении отображаемого имени администратора")
        await message.answer(f"❌ Произошла ошибка при обновлении отображаемого имени: {str(e)}", reply_markup=admins_menu_kb)
    finally:
        await state.clear()
    log_debug(logger, "Выход из process_new_admin_display_name")

