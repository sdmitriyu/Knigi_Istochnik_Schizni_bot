from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from data.models import Books, Order, Greeting, Admin, OrderStatus
from config.keyboards import commands, books_menu_kb, orders_menu_kb, texts_menu_kb, admins_menu_kb, greetings_kb # Обновил импорты клавиатур
from config.static import HELP_TEXT
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from admin.state_book import BookState, OrderAdminState, BookEditState # Добавляем импорт BookEditState
from typing import cast # Добавляем импорт cast
from config.logger_config import setup_logger, log_debug, log_info, log_error

admin_router = Router()

logger = setup_logger('admin_state_book_handlers')

async def is_admin_filter(message: Message) -> bool:
    if not message.from_user:
        log_debug(logger, "is_admin_filter: Отсутствует информация о пользователе.", {})
        return False
    
    user_id = message.from_user.id
    is_admin = Admin.get_or_none(Admin.user_id == user_id) is not None
    log_debug(logger, f"is_admin_filter: Проверка пользователя {user_id}. Результат: {is_admin}", {"user_id": user_id, "is_admin": is_admin})
    return is_admin

admin_router.message.filter(is_admin_filter)

@admin_router.message(Command("start"))
async def start(message: Message):
    log_debug(logger, "Вход в обработчик start", {"user_id": message.from_user.id if message.from_user else None})
    try:
        if not message.from_user:
            log_error(logger, Exception("Нет from_user"), "start: Нет from_user")
            return
        await message.answer("Очищаю предыдущую клавиатуру...", reply_markup=ReplyKeyboardRemove())
        await message.answer("👋 Добро пожаловать в административное меню! Выберите действие:", reply_markup=commands)
    except Exception as e:
        log_error(logger, e, "Ошибка в start")

@admin_router.message(Command("help"))
async def help_command(message: Message):
    log_debug(logger, "Вход в обработчик help_command", {"user_id": message.from_user.id if message.from_user else None})
    try:
        await message.answer(HELP_TEXT, parse_mode="Markdown", reply_markup=commands)
    except Exception as e:
        log_error(logger, e, "Ошибка в help_command")

# Новые обработчики для навигации по меню
@admin_router.message(F.text == "📚 Управление книгами")
async def manage_books(message: Message):
    log_debug(logger, "Вход в обработчик manage_books", {"user_id": message.from_user.id if message.from_user else None})
    try:
        await message.answer("📚 Вы перешли в раздел управления книгами.", reply_markup=books_menu_kb)
    except Exception as e:
        log_error(logger, e, "Ошибка в manage_books")
        await message.answer("❌ Произошла ошибка при переходе в раздел управления книгами.", reply_markup=books_menu_kb)

@admin_router.message(F.text == "📦 Управление заказами")
async def manage_orders(message: Message):
    await message.answer("📦 Вы перешли в раздел управления заказами.", reply_markup=orders_menu_kb)

@admin_router.message(F.text == "👥 Управление администраторами")
async def manage_admins(message: Message):
    await message.answer("👥 Вы перешли в раздел управления администраторами.", reply_markup=admins_menu_kb)

@admin_router.message(F.text == "📝 Управление текстами")
async def manage_texts(message: Message):
    await message.answer("📝 Вы перешли в раздел управления текстами.", reply_markup=texts_menu_kb)

@admin_router.message(F.text == "🏠 Назад в главное меню")
async def back_to_main_menu(message: Message, state: FSMContext):
    await state.clear() # Очищаем состояние при возвращении в главное меню
    await message.answer("🏠 Вы вернулись в главное меню.", reply_markup=commands)

@admin_router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("❌ Нет активных действий для отмены.", reply_markup=commands)
        return
    
    await state.clear()
    await message.answer(
        "✅ Действие отменено. Вы вернулись в главное меню.",
        reply_markup=commands
    )

@admin_router.message(F.text == "📚 Показать книги")
async def show_books_with_inline_buttons(message: Message):
    books = Books.select()
    if not books:
        await message.answer("📚 В базе данных пока нет книг.", reply_markup=books_menu_kb)
        return
        
    for book in books:
        if book.photo:
            await message.answer_photo(book.photo)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Изменить книгу", callback_data=f"edit_book_{book.id}"),
             InlineKeyboardButton(text="🗑 Удалить книгу", callback_data=f"delete_book_{book.id}")]
        ])
        
        await message.answer(
            f"📚 *{book.name}*\n"
            f"✍️ Автор: {book.author}\n"
            f"💰 Цена: {book.price} руб.\n"
            f"📦 В наличии: {book.quantity} шт.\n"
            f"📝 Описание: {book.description}",
            parse_mode="Markdown",
            reply_markup=keyboard
        )
    await message.answer("📚 Выберите действие:", reply_markup=books_menu_kb)

@admin_router.message(F.text == "➕ Добавить книгу")
async def add_book(message: Message, state: FSMContext):
    await state.set_state(BookState.name)
    await message.answer("📚 Введите название книги:", reply_markup=books_menu_kb)

@admin_router.message(BookState.name)   
async def process_book_name(message: Message, state: FSMContext):
    if not message.text or len(message.text.strip()) < 2:
        await message.answer("❌ Название книги должно содержать минимум 2 символа. Попробуйте еще раз:", reply_markup=books_menu_kb)
        return
        
    await state.update_data(name=message.text.strip())
    await state.set_state(BookState.author)
    await message.answer("✍️ Введите автора книги:", reply_markup=books_menu_kb)

@admin_router.message(BookState.author) 
async def process_book_author(message: Message, state: FSMContext):
    if not message.text or len(message.text.strip()) < 2:
        await message.answer("❌ Имя автора должно содержать минимум 2 символа. Попробуйте еще раз:", reply_markup=books_menu_kb)
        return
        
    await state.update_data(author=message.text.strip())
    await state.set_state(BookState.price)
    await message.answer("💰 Введите цену книги (только число):")

@admin_router.message(BookState.price)  
async def process_book_price(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("💰 Пожалуйста, введите цену книги:", reply_markup=books_menu_kb)
        return
    try:
        price = float(message.text.replace(',', '.'))
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Пожалуйста, введите корректную цену (положительное число). Попробуйте еще раз:", reply_markup=books_menu_kb)
        return
        
    await state.update_data(price=price)
    await state.set_state(BookState.description)
    await message.answer("📝 Введите описание книги:", reply_markup=books_menu_kb)

@admin_router.message(BookState.description)    
async def process_book_description(message: Message, state: FSMContext):
    if not message.text or len(message.text.strip()) < 10:
        await message.answer("❌ Описание должно содержать минимум 10 символов. Попробуйте еще раз:", reply_markup=books_menu_kb)
        return
        
    await state.update_data(description=message.text.strip())
    await state.set_state(BookState.photo)
    await message.answer("🖼 Отправьте фото книги:", reply_markup=books_menu_kb)

@admin_router.message(BookState.photo)  
async def process_book_photo(message: Message, state: FSMContext):
    if not message.photo:
        await message.answer("❌ Пожалуйста, отправьте фото книги:", reply_markup=books_menu_kb)
        return
        
    await state.update_data(photo=message.photo[-1].file_id)
    await state.set_state(BookState.quantity)
    await message.answer("📦 Введите количество книг (целое число):")

@admin_router.message(BookState.quantity)   
async def process_book_quantity(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("📦 Пожалуйста, введите количество книг:", reply_markup=books_menu_kb)
        return
    try:
        quantity = int(message.text)
        if quantity < 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Пожалуйста, введите корректное количество (целое положительное число). Попробуйте еще раз:", reply_markup=books_menu_kb)
        return
        
    await state.update_data(quantity=quantity)
    data = await state.get_data()
    
    try:
        book = Books.create(
            name=data["name"],
            author=data["author"],
            price=data["price"],
            description=data["description"],
            photo=data["photo"],
            quantity=data["quantity"]
        )
        await message.answer(
            "✅ Книга успешно добавлена в базу данных!\n\n"
            "📚 Чтобы добавить еще одну книгу, нажмите '➕ Добавить книгу'\n"
            "🏠 Чтобы вернуться в главное меню, используйте /start",
            reply_markup=books_menu_kb
        )
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка при сохранении книги: {str(e)}", reply_markup=books_menu_kb)
    
    await state.clear()

@admin_router.message(F.text == "📋 Все заказы")
async def view_orders(message: Message):
    orders = Order.select().order_by(Order.id.desc())
    if not orders:
        await message.answer("📦 В базе данных пока нет заказов.", reply_markup=orders_menu_kb)
        return
    
    for order in orders:
        book_info_str = order.book_info if order.book_info else "Информация о книге недоступна"
        status = order.status
        
        # Создаем инлайн-клавиатуру для каждого заказа
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Изменить статус", callback_data=f"change_status_{order.id}"),
             InlineKeyboardButton(text="🗑️ Удалить заказ", callback_data=f"delete_order_{order.id}")]
        ])
        
        await message.answer(
            f"📦 *Заказ №{order.id}*\n"
            f"👤 ФИО: {order.fio}\n"
            f"🏠 Адрес: {order.addres}\n"
            f"📞 Телефон: {order.phone}\n"
            f"📚 Книга: {book_info_str}\n"
            f"📊 Статус: {status.emoji} {status.description}\n"
            f"📅 Создан: {order.created_at.strftime('%d.%m.%Y %H:%M')}\n"
            f"🔄 Обновлен: {order.updated_at.strftime('%d.%m.%Y %H:%M')}",
            parse_mode="Markdown",
            reply_markup=keyboard
        )
    await message.answer("📦 Выберите действие с заказами:", reply_markup=orders_menu_kb)

@admin_router.message(F.text == "🆕 Новые заказы")
async def view_new_orders(message: Message):
    await message.answer("Эта функция находится в разработке.", reply_markup=orders_menu_kb)

# Новый обработчик для выбора заказа через инлайн-кнопку
@admin_router.callback_query(F.data.startswith("change_status_"))
async def select_order_for_status_change(callback_query: CallbackQuery):
    if not callback_query.data:
        await callback_query.answer("❌ Ошибка данных коллбэка.", show_alert=True)
        return

    # Явно приводим data к строке после проверки на None
    data_string: str = callback_query.data
    order_id = int(data_string.split("_")[2])
    order = Order.get_or_none(Order.id == order_id)
    
    if not order:
        await callback_query.answer("❌ Заказ не найден.", show_alert=True)
        return
    
    statuses = OrderStatus.select()
    status_buttons = []
    for status in statuses:
        status_buttons.append(InlineKeyboardButton(text=f"{status.emoji} {status.description}", callback_data=f"set_status_{status.id}_{order_id}"))
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[status_buttons])
    
    if callback_query.message:
        message_obj = cast(Message, callback_query.message) # Явное приведение к типу Message
        await message_obj.answer(
            f"📊 Текущий статус заказа №{order_id}: {order.status.emoji} {order.status.description}\n\n"
            "Выберите новый статус:",
            reply_markup=keyboard
        )
    else:
        await callback_query.answer("Выберите новый статус:", show_alert=True)
    
    await callback_query.answer() # Отвечаем на коллбэк

# Новый обработчик для установки нового статуса
@admin_router.callback_query(F.data.startswith("set_status_"))
async def set_order_status(callback_query: CallbackQuery):
    if not callback_query.data:
        await callback_query.answer("❌ Ошибка данных коллбэка.", show_alert=True)
        return

    data_string: str = callback_query.data
    parts = data_string.split("_")
    if len(parts) < 3:
        await callback_query.answer("❌ Некорректный формат данных коллбэка.", show_alert=True)
        return

    new_status_id = int(parts[1])
    order_id = int(parts[2])
    
    order = Order.get_or_none(Order.id == order_id)
    new_status = OrderStatus.get_or_none(id=new_status_id)
    
    if not order or not new_status:
        await callback_query.answer("❌ Ошибка: заказ или статус не найден.", show_alert=True)
        return
        
    try:
        old_status = order.status
        order.status = new_status
        order.save()
        
        status_message = (
            f"✅ Статус заказа №{order_id} изменен:\n"
            f"С {old_status.emoji} {old_status.description}\n"
            f"На {new_status.emoji} {new_status.description}"
        )
        
        if callback_query.message:
            message_obj = cast(Message, callback_query.message) # Явное приведение к типу Message
            await message_obj.answer(status_message)
        else:
            await callback_query.answer(status_message, show_alert=True)
        
        # Отправляем уведомление пользователю
        user_telegram_id = order.telegram_id
        if callback_query.bot:
            try:
                client_message = (
                    f"🔔 *Обновление статуса заказа №{order.id}*\n\n"
                    f"{new_status.emoji} {new_status.client_message}"
                )
                await callback_query.bot.send_message(
                    user_telegram_id,
                    client_message,
                    parse_mode="Markdown"
                )
                if callback_query.message:
                    message_obj = cast(Message, callback_query.message) # Явное приведение к типу Message
                    await message_obj.answer("✅ Уведомление отправлено пользователю.")
                else:
                    await callback_query.answer("✅ Уведомление отправлено пользователю.", show_alert=True)
            except Exception as e:
                if callback_query.message:
                    message_obj = cast(Message, callback_query.message) # Явное приведение к типу Message
                    await message_obj.answer(
                        f"❌ Не удалось отправить уведомление пользователю (ID: {user_telegram_id}): {str(e)}"
                    )
                else:
                    await callback_query.answer(f"❌ Не удалось отправить уведомление пользователю (ID: {user_telegram_id}): {str(e)}", show_alert=True)
        else:
            if callback_query.message:
                message_obj = cast(Message, callback_query.message) # Явное приведение к типу Message
                await message_obj.answer("❌ Не удалось получить объект бота для отправки уведомления.")
            else:
                await callback_query.answer("❌ Не удалось получить объект бота для отправки уведомления.", show_alert=True)
            
    except Exception as e:
        if callback_query.message:
            message_obj = cast(Message, callback_query.message) # Явное приведение к типу Message
            await message_obj.answer(f"❌ Произошла ошибка при изменении статуса заказа: {str(e)}")
        else:
            await callback_query.answer(f"❌ Произошла ошибка при изменении статуса заказа: {str(e)}", show_alert=True)
    
    await callback_query.answer() # Отвечаем на коллбэк

@admin_router.callback_query(F.data.startswith("edit_book_"))
async def edit_book_callback_handler(callback_query: CallbackQuery, state: FSMContext):
    if not callback_query.data:
        await callback_query.answer("❌ Ошибка данных коллбэка.", show_alert=True)
        return

    book_id = int(callback_query.data.split("_")[2])
    book = Books.get_or_none(Books.id == book_id)

    if not book:
        await callback_query.answer("❌ Книга не найдена.", show_alert=True)
        return

    await state.update_data(book_id=book_id)
    await state.set_state(BookEditState.edit_field)

    edit_options_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Изменить название", callback_data=f"edit_field_name")],
        [InlineKeyboardButton(text="Изменить автора", callback_data=f"edit_field_author")],
        [InlineKeyboardButton(text="Изменить описание", callback_data=f"edit_field_description")],
        [InlineKeyboardButton(text="Изменить цену", callback_data=f"edit_field_price")],
        [InlineKeyboardButton(text="Изменить количество", callback_data=f"edit_field_quantity")],
        [InlineKeyboardButton(text="Изменить фото", callback_data=f"edit_field_photo")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data=f"cancel_edit_book")]
    ])

    if callback_query.message:
        message_obj = cast(Message, callback_query.message)
        await message_obj.answer(
            f"✏️ Выбрана книга: *{book.name}*\n\n"
            "Выберите поле для редактирования:",
            reply_markup=edit_options_keyboard
        )
    else:
        await callback_query.answer("Выберите поле для редактирования:", show_alert=True)

    await callback_query.answer()

@admin_router.callback_query(F.data.startswith("delete_book_"))
async def delete_book_callback_handler(callback_query: CallbackQuery, state: FSMContext):
    if not callback_query.data:
        await callback_query.answer("❌ Ошибка данных коллбэка.", show_alert=True)
        return

    book_id = int(callback_query.data.split("_")[2])
    book = Books.get_or_none(Books.id == book_id)

    if not book:
        await callback_query.answer("❌ Книга не найдена.", show_alert=True)
        return

    confirm_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"confirm_delete_book_{book.id}"),
         InlineKeyboardButton(text="❌ Нет, отмена", callback_data=f"cancel_delete_book")]
    ])

    if callback_query.message:
        message_obj = cast(Message, callback_query.message)
        await message_obj.answer(
            f"🗑 Вы действительно хотите удалить книгу *{book.name}*?",
            reply_markup=confirm_keyboard
        )
    else:
        await callback_query.answer("Подтвердите удаление книги.", show_alert=True)
    
    await callback_query.answer()

@admin_router.callback_query(F.data.startswith("confirm_delete_book_"))
async def confirm_delete_book_callback_handler(callback_query: CallbackQuery):
    if not callback_query.data:
        await callback_query.answer("❌ Ошибка данных коллбэка.", show_alert=True)
        return

    book_id = int(callback_query.data.split("_")[3])

    try:
        book = Books.get_or_none(Books.id == book_id)
        if not book:
            await callback_query.answer("❌ Книга не найдена.", show_alert=True)
            return
        
        book_name = book.name
        book.delete_instance()
        
        if callback_query.message:
            message_obj = cast(Message, callback_query.message)
            await message_obj.edit_text(f"✅ Книга *{book_name}* успешно удалена.")
        await callback_query.answer(f"✅ Книга {book_name} успешно удалена.")

    except Exception as e:
        print(f"DEBUG: Error in confirm_delete_book_callback_handler: {e}")
        await callback_query.answer(f"❌ Произошла ошибка при удалении книги: {str(e)}", show_alert=True)

@admin_router.callback_query(F.data == "cancel_delete_book")
async def cancel_delete_book_callback_handler(callback_query: CallbackQuery):
    if callback_query.message:
        message_obj = cast(Message, callback_query.message)
        await message_obj.edit_text("❌ Удаление книги отменено.")
    await callback_query.answer("Удаление книги отменено.")

@admin_router.callback_query(F.data == "cancel_edit_book")
async def cancel_edit_book_callback_handler(callback_query: CallbackQuery, state: FSMContext):
    await state.clear()
    if callback_query.message:
        message_obj = cast(Message, callback_query.message)
        await message_obj.edit_text("❌ Редактирование книги отменено.")
    await callback_query.answer("Редактирование книги отменено.")

# Обработчики для выбора поля для редактирования
@admin_router.callback_query(F.data.startswith("edit_field_"))
async def choose_edit_field_callback_handler(callback_query: CallbackQuery, state: FSMContext):
    if not callback_query.data:
        await callback_query.answer("❌ Ошибка данных коллбэка.", show_alert=True)
        return

    field_to_edit = callback_query.data.split("_")[2]
    current_data = await state.get_data()
    book_id = current_data.get("book_id")

    if not book_id:
        await callback_query.answer("❌ ID книги для редактирования не найден.", show_alert=True)
        return

    book = Books.get_or_none(Books.id == book_id)
    if not book:
        await callback_query.answer("❌ Книга не найдена.", show_alert=True)
        await state.clear()
        return

    if not callback_query.message:
        await callback_query.answer("❌ Не удалось получить информацию о сообщении.", show_alert=True)
        return
    
    message_obj = cast(Message, callback_query.message)

    # Установка соответствующего состояния FSM и запрос нового значения
    if field_to_edit == "name":
        await state.set_state(BookEditState.new_name)
        await message_obj.answer(f"Введите новое название для книги *{book.name}*:")
    elif field_to_edit == "author":
        await state.set_state(BookEditState.new_author)
        await message_obj.answer(f"Введите нового автора для книги *{book.name}*:")
    elif field_to_edit == "description":
        await state.set_state(BookEditState.new_description)
        await message_obj.answer(f"Введите новое описание для книги *{book.name}*:")
    elif field_to_edit == "price":
        await state.set_state(BookEditState.new_price)
        await message_obj.answer(f"Введите новую цену для книги *{book.name}* (только число):")
    elif field_to_edit == "quantity":
        await state.set_state(BookEditState.new_quantity)
        await message_obj.answer(f"Введите новое количество для книги *{book.name}* (целое число):")
    elif field_to_edit == "photo":
        await state.set_state(BookEditState.new_photo)
        await message_obj.answer(f"Отправьте новое фото для книги *{book.name}*:")
    else:
        await callback_query.answer("❌ Неизвестное поле для редактирования.", show_alert=True)
        return

    await callback_query.answer()

@admin_router.message(F.text == "❌ Отмена")
async def cancel_action(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("❌ Нет активных действий для отмены.", reply_markup=commands)
        return
    
    await state.clear()
    await message.answer(
        "✅ Действие отменено. Вы вернулись в главное меню.",
        reply_markup=books_menu_kb # Возвращаемся в меню книг
    )

# Обработчики для обновления данных книги
@admin_router.message(BookEditState.new_name)
async def process_new_book_name(message: Message, state: FSMContext):
    if not message.text or len(message.text.strip()) < 2:
        await message.answer("❌ Название книги должно содержать минимум 2 символа. Попробуйте еще раз:")
        return
    
    data = await state.get_data()
    book_id = data.get("book_id")
    book = Books.get_or_none(Books.id == book_id)

    if not book:
        await message.answer("❌ Книга не найдена. Пожалуйста, начните редактирование заново.")
        await state.clear()
        return

    try:
        book.name = message.text.strip()
        book.save()
        await message.answer(f"✅ Название книги *{book.name}* успешно обновлено!")
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка при обновлении названия: {str(e)}")
    finally:
        await state.clear()

@admin_router.message(BookEditState.new_author)
async def process_new_book_author(message: Message, state: FSMContext):
    if not message.text or len(message.text.strip()) < 2:
        await message.answer("❌ Имя автора должно содержать минимум 2 символа. Попробуйте еще раз:")
        return
    
    data = await state.get_data()
    book_id = data.get("book_id")
    book = Books.get_or_none(Books.id == book_id)

    if not book:
        await message.answer("❌ Книга не найдена. Пожалуйста, начните редактирование заново.")
        await state.clear()
        return

    try:
        book.author = message.text.strip()
        book.save()
        await message.answer(f"✅ Автор книги *{book.name}* успешно обновлен!")
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка при обновлении автора: {str(e)}")
    finally:
        await state.clear()

@admin_router.message(BookEditState.new_description)
async def process_new_book_description(message: Message, state: FSMContext):
    if not message.text or len(message.text.strip()) < 10:
        await message.answer("❌ Описание должно содержать минимум 10 символов. Попробуйте еще раз:")
        return
    
    data = await state.get_data()
    book_id = data.get("book_id")
    book = Books.get_or_none(Books.id == book_id)

    if not book:
        await message.answer("❌ Книга не найдена. Пожалуйста, начните редактирование заново.")
        await state.clear()
        return

    try:
        book.description = message.text.strip()
        book.save()
        await message.answer(f"✅ Описание книги *{book.name}* успешно обновлено!")
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка при обновлении описания: {str(e)}")
    finally:
        await state.clear()

@admin_router.message(BookEditState.new_price)
async def process_new_book_price(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("💰 Пожалуйста, введите цену книги (только число):")
        return
    try:
        price = float(message.text.replace(',', '.'))
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Пожалуйста, введите корректную цену (положительное число). Попробуйте еще раз:")
        return
    
    data = await state.get_data()
    book_id = data.get("book_id")
    book = Books.get_or_none(Books.id == book_id)

    if not book:
        await message.answer("❌ Книга не найдена. Пожалуйста, начните редактирование заново.")
        await state.clear()
        return

    try:
        book.price = price
        book.save()
        await message.answer(f"✅ Цена книги *{book.name}* успешно обновлена!")
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка при обновлении цены: {str(e)}")
    finally:
        await state.clear()

@admin_router.message(BookEditState.new_quantity)
async def process_new_book_quantity(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("📦 Пожалуйста, введите количество книг (целое число):")
        return
    try:
        quantity = int(message.text)
        if quantity < 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Пожалуйста, введите корректное количество (целое положительное число). Попробуйте еще раз:")
        return
    
    data = await state.get_data()
    book_id = data.get("book_id")
    book = Books.get_or_none(Books.id == book_id)

    if not book:
        await message.answer("❌ Книга не найдена. Пожалуйста, начните редактирование заново.")
        await state.clear()
        return

    try:
        book.quantity = quantity
        book.save()
        await message.answer(f"✅ Количество книг *{book.name}* успешно обновлено!")
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка при обновлении количества: {str(e)}")
    finally:
        await state.clear()

@admin_router.message(BookEditState.new_photo)
async def process_new_book_photo(message: Message, state: FSMContext):
    if not message.photo:
        await message.answer("❌ Пожалуйста, отправьте фото книги:")
        return
    
    data = await state.get_data()
    book_id = data.get("book_id")
    book = Books.get_or_none(Books.id == book_id)

    if not book:
        await message.answer("❌ Книга не найдена. Пожалуйста, начните редактирование заново.")
        await state.clear()
        return

    try:
        book.photo = message.photo[-1].file_id
        book.save()
        await message.answer(f"✅ Фото книги *{book.name}* успешно обновлено!")
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка при обновлении фото: {str(e)}")
    finally:
        await state.clear()

# Обработчики для удаления заказа
@admin_router.callback_query(F.data.startswith("delete_order_"))
async def delete_order_callback_handler(callback_query: CallbackQuery):
    if not callback_query.data:
        await callback_query.answer("❌ Ошибка данных коллбэка.", show_alert=True)
        return

    order_id = int(callback_query.data.split("_")[2])
    order = Order.get_or_none(Order.id == order_id)

    if not order:
        await callback_query.answer("❌ Заказ не найден.", show_alert=True)
        return

    confirm_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"confirm_delete_order_{order.id}"),
         InlineKeyboardButton(text="❌ Нет, отмена", callback_data=f"cancel_delete_order")]
    ])

    if callback_query.message:
        message_obj = cast(Message, callback_query.message)
        await message_obj.answer(
            f"🗑️ Вы действительно хотите удалить заказ №{order.id}?",
            reply_markup=confirm_keyboard
        )
    else:
        await callback_query.answer("Подтвердите удаление заказа.", show_alert=True)
    
    await callback_query.answer()

@admin_router.callback_query(F.data.startswith("confirm_delete_order_"))
async def confirm_delete_order_callback_handler(callback_query: CallbackQuery):
    if not callback_query.data:
        await callback_query.answer("❌ Ошибка данных коллбэка.", show_alert=True)
        return

    order_id = int(callback_query.data.split("_")[3])

    try:
        order = Order.get_or_none(Order.id == order_id)
        if not order:
            await callback_query.answer("❌ Заказ не найден.", show_alert=True)
            return
        
        order.delete_instance()
        
        if callback_query.message:
            message_obj = cast(Message, callback_query.message)
            await message_obj.edit_text(f"✅ Заказ №{order_id} успешно удален.")
        await callback_query.answer(f"✅ Заказ №{order_id} успешно удален.")

    except Exception as e:
        print(f"DEBUG: Error in confirm_delete_order_callback_handler: {e}")
        await callback_query.answer(f"❌ Произошла ошибка при удалении заказа: {str(e)}", show_alert=True)

@admin_router.callback_query(F.data == "cancel_delete_order")
async def cancel_delete_order_callback_handler(callback_query: CallbackQuery):
    if callback_query.message:
        message_obj = cast(Message, callback_query.message)
        await message_obj.edit_text("❌ Удаление заказа отменено.")
    await callback_query.answer("Удаление заказа отменено.")


