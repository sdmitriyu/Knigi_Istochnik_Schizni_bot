from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, InaccessibleMessage
from aiogram.filters import Command
from data.models import Greeting, Admin, Dialog
from config.keyboards import greetings_kb
from data.models import Books
from config.state_order_handlers import AskQuestionState
from aiogram.fsm.context import FSMContext
from typing import cast, Optional, Union
from datetime import datetime, timedelta
from config.logger_config import setup_logger, log_error, log_info, log_debug, log_warning

# Настройка логгера
logger = setup_logger('handlers')

router = Router()

# Словарь для защиты от спама: {user_id: last_message_time}
spam_protection: dict[int, datetime] = {}

def is_spam(user_id: int) -> bool:
    """Проверяет, не спамит ли пользователь"""
    try:
        current_time = datetime.now()
        if user_id in spam_protection:
            last_message_time = spam_protection[user_id]
            if current_time - last_message_time < timedelta(seconds=5):  # 5 секунд между сообщениями
                log_warning(logger, f"Обнаружен спам от пользователя {user_id}")
                return True
        spam_protection[user_id] = current_time
        return False
    except Exception as e:
        log_error(logger, e, f"Ошибка при проверке спама для пользователя {user_id}")
        return False

@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    try:
        if not message.from_user:
            log_warning(logger, "Получено сообщение без информации о пользователе")
            return
            
        log_debug(logger, "Обработка команды /start", {"user_id": message.from_user.id})
            
        # Check if the user is an admin. If so, let the admin_router handle it.
        if Admin.get_or_none(Admin.user_id == message.from_user.id):
            log_debug(logger, "Пользователь является администратором", {"user_id": message.from_user.id})
            return # Do not send a keyboard if the user is an admin

        great = Greeting.get_or_none()
        if great:
            log_debug(logger, "Отправка приветствия", {"text": great.text[:50] + "..."})
            await message.answer(great.text, reply_markup=greetings_kb)
        else:
            log_warning(logger, "Приветствие не найдено в базе данных")
            await message.answer("Добро пожаловать!", reply_markup=greetings_kb)
    except Exception as e:
        log_error(logger, e, "Ошибка в обработчике start")
        await message.answer("Произошла ошибка. Пожалуйста, попробуйте позже.")

@router.message(Command("help"))
async def help(message: Message) -> None:
    try:
        if not message.from_user:
            log_warning(logger, "Получено сообщение без информации о пользователе")
            return
            
        log_debug(logger, "Обработка команды /help", {"user_id": message.from_user.id})
            
        help_text = (
            "📚 *Бот книжного магазина*\n\n"
            "*Основные команды:*\n"
            "/start - Начать взаимодействие с ботом\n"
            "/help - Показать эту справку\n\n"
            "*Функционал:*\n"
            "1. *Галерея книг* 📚\n"
            "   - Просмотр доступных книг\n"
            "   - Описание и фотографии\n"
            "   - Информация о наличии\n\n"
            "2. *Оформление заказа* 🛒\n"
            "   - Выбор книги\n"
            "   - Указание контактных данных\n"
            "   - Отслеживание статуса заказа\n\n"
            "3. *Связаться с администратором* 💬\n"
            "   - Задать вопрос\n"
            "   - Получить консультацию\n"
            "   - Обсудить детали заказа\n\n"
            "4. *Техподдержка* 🛠\n"
            "   - Решение технических проблем\n"
            "   - Помощь с использованием бота\n\n"
            "*Статусы заказа:*\n"
            "🆕 Новый заказ\n"
            "⚙️ В обработке\n"
            "📢 Поставщик уведомлен\n"
            "📦 Книга забрана\n"
            "🚚 В пути\n"
            "✅ Доставлен\n"
            "❌ Отменен\n\n"
            "*Важно:*\n"
            "• Заказы обрабатываются в рабочее время\n"
            "• Ответы на вопросы в течение 24 часов\n"
            "• При возникновении проблем обращайтесь в техподдержку"
        )
        
        log_debug(logger, "Отправка справки", {"user_id": message.from_user.id})
        await message.answer(help_text, parse_mode="Markdown")
    except Exception as e:
        log_error(logger, e, "Ошибка в обработчике help")
        await message.answer("Произошла ошибка. Пожалуйста, попробуйте позже.")

@router.callback_query(F.data == "books_gallery")
async def go_in_gallery(callback: CallbackQuery) -> None:
    try:
        if not callback.message or isinstance(callback.message, InaccessibleMessage):
            log_warning(logger, "Получен недоступный callback message")
            await callback.answer()
            return
            
        log_debug(logger, "Обработка запроса галереи книг", {"user_id": callback.from_user.id})
            
        books = Books.select()
        if not books:
            log_warning(logger, "В базе нет книг")
            message_obj = cast(Message, callback.message)
            await message_obj.answer(text="В базе нет книг.")
            await callback.answer()
            return
        
        for book in books:
            try:
                log_debug(logger, "Отправка информации о книге", {
                    "book_id": book.id,
                    "name": book.name,
                    "user_id": callback.from_user.id
                })
                
                if book.photo:
                    # Отправляем фото, если оно есть
                    message_obj = cast(Message, callback.message)
                    await message_obj.answer_photo(book.photo)
                
                order_kb = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text=f"Заказать {book.name}", callback_data=f"order_book_{book.id}")]
                    ]
                )
                message_obj = cast(Message, callback.message)
                await message_obj.answer(
                    f"📚 *{book.name}*\n"
                    f"✍️ Автор: {book.author}\n"
                    f"💰 Цена: {book.price} руб.\n"
                    f"📦 В наличии: {book.quantity} шт.\n"
                    f"📝 Описание: {book.description}",
                    parse_mode="Markdown",
                    reply_markup=order_kb
                )
            except Exception as e:
                log_error(logger, e, f"Ошибка при отправке информации о книге {book.id}")
                continue
        
        message_obj = cast(Message, callback.message)
        await message_obj.answer("Выберите действие:")
        await callback.answer()
    except Exception as e:
        log_error(logger, e, "Ошибка в обработчике books_gallery")
        if callback.message and not isinstance(callback.message, InaccessibleMessage):
            message_obj = cast(Message, callback.message)
            await message_obj.answer("Произошла ошибка при загрузке каталога. Пожалуйста, попробуйте позже.")
        await callback.answer()

@router.callback_query(F.data.startswith("order_book_"))
async def process_order(callback: CallbackQuery):
    if not callback.data:
        log_warning(logger, "Получен пустой callback_data")
        await callback.answer()
        return
        
    # Получаем ID книги из callback_data
    try:
        book_id = int(callback.data.split("_")[-1])
        log_debug(logger, "Обработка заказа книги", {
            "book_id": book_id,
            "user_id": callback.from_user.id
        })
    except (ValueError, IndexError):
        log_error(logger, ValueError("Неверный формат callback_data"), f"callback_data: {callback.data}")
        if callback.message and isinstance(callback.message, Message) and not isinstance(callback.message, InaccessibleMessage):
            await callback.message.answer("Ошибка при обработке заказа")
        await callback.answer()
        return
    
    # Получаем информацию о книге
    book = Books.get_or_none(Books.id == book_id)
    if not book:
        log_warning(logger, f"Книга не найдена", {"book_id": book_id})
        if callback.message and isinstance(callback.message, Message) and not isinstance(callback.message, InaccessibleMessage):
            await callback.message.answer("Книга не найдена")
        await callback.answer()
        return
    
    # Здесь можно добавить логику оформления заказа
    if callback.message and isinstance(callback.message, Message) and not isinstance(callback.message, InaccessibleMessage):
        log_debug(logger, "Отправка формы заказа", {
            "book_id": book.id,
            "name": book.name,
            "user_id": callback.from_user.id
        })
        await callback.message.answer(
            f"Вы выбрали книгу:\n"
            f"Название: {book.name}\n"
            f"Автор: {book.author}\n"
            f"Цена: {book.price} руб.\n\n"
            f"Для оформления заказа введите свои данные в формате:\n"
            f"ФИО, адрес, телефон"
        )
    await callback.answer()

# Новый обработчик для кнопки "Задать вопрос"
@router.callback_query(F.data == "ask_question_start")
async def ask_question_start(callback: CallbackQuery, state: FSMContext):
    try:
        if not callback.message or isinstance(callback.message, InaccessibleMessage):
            log_warning(logger, "Получен недоступный callback message в ask_question_start")
            await callback.answer()
            return
            
        log_debug(logger, "Начало процесса задавания вопроса", {"user_id": callback.from_user.id})
        
        message_obj = cast(Message, callback.message)

        # Получаем всех администраторов, кроме техподдержки
        admins = Admin.select().where(Admin.role == 'admin')
        
        keyboard_buttons = []
        for admin in admins:
            if admin.display_name:
                keyboard_buttons.append([InlineKeyboardButton(text=admin.display_name, callback_data=f"select_admin_for_question_{admin.user_id}")])
        
        if not keyboard_buttons:
            log_warning(logger, "Нет доступных администраторов для вопросов", {})
            await message_obj.answer("Извините, администраторы для вопросов сейчас недоступны.")
            await callback.answer()
            return

        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        await state.set_state(AskQuestionState.choose_admin) # Устанавливаем состояние выбора администратора
        
        await message_obj.answer("Выберите администратора для вашего вопроса:", reply_markup=keyboard)
        await callback.answer()
    except Exception as e:
        log_error(logger, e, "Ошибка в обработчике ask_question_start")
        if callback.message and not isinstance(callback.message, InaccessibleMessage):
            message_obj = cast(Message, callback.message)
            await message_obj.answer("Произошла ошибка при выборе администратора. Пожалуйста, попробуйте позже.")
        await callback.answer()

@router.callback_query(AskQuestionState.choose_admin, F.data.startswith("select_admin_for_question_"))
async def select_admin_for_question(callback: CallbackQuery, state: FSMContext):
    try:
        if not callback.message or isinstance(callback.message, InaccessibleMessage):
            log_warning(logger, "Получен недоступный callback message в select_admin_for_question")
            await callback.answer()
            return

        message_obj = cast(Message, callback.message)
        
        if not callback.data:
            log_warning(logger, "Получен пустой callback_data в select_admin_for_question", {})
            await message_obj.answer("Произошла ошибка при выборе администратора.")
            await callback.answer()
            return

        try:
            admin_user_id = int(callback.data.split("_")[-1])
            log_debug(logger, "Выбран администратор для вопроса", {"admin_user_id": admin_user_id, "user_id": callback.from_user.id})
        except (ValueError, IndexError):
            log_error(logger, ValueError("Неверный формат callback_data для выбора администратора"), f"callback_data: {callback.data}")
            await message_obj.answer("Произошла ошибка при выборе администратора.")
            await callback.answer()
            return

        admin = Admin.get_or_none(Admin.user_id == admin_user_id)
        if not admin:
            log_warning(logger, "Выбранный администратор не найден", {"admin_user_id": admin_user_id})
            await message_obj.answer("Выбранный администратор не найден. Пожалуйста, попробуйте еще раз.")
            await callback.answer()
            return
        
        await state.update_data(selected_admin_id=admin_user_id)
        await state.set_state(AskQuestionState.input_question)
        
        await message_obj.answer(f"Вы выбрали администратора {admin.display_name or admin.user_name}. Теперь, пожалуйста, введите ваш вопрос:")
        await callback.answer()
    except Exception as e:
        log_error(logger, e, "Ошибка в обработчике select_admin_for_question")
        if callback.message and not isinstance(callback.message, InaccessibleMessage):
            message_obj = cast(Message, callback.message)
            await message_obj.answer("Произошла ошибка при выборе администратора. Пожалуйста, попробуйте позже.")
        await callback.answer()

# Новый обработчик для ввода вопроса пользователем
@router.message(AskQuestionState.input_question)
async def process_user_question(message: Message, state: FSMContext):
    try:
        if not message.from_user or not message.text:
            log_warning(logger, "Получено сообщение без пользователя или текста в process_user_question")
            return
            
        user_id = message.from_user.id
        question_text = message.text
        
        log_debug(logger, "Получен вопрос от пользователя", {"user_id": user_id, "question": question_text[:50] + "..."})

        data = await state.get_data()
        selected_admin_id = data.get('selected_admin_id')

        if not selected_admin_id:
            log_error(logger, ValueError("ID выбранного администратора не найден в состоянии"), f"user_id: {user_id}")
            await message.answer("Произошла ошибка при отправке вопроса. Пожалуйста, попробуйте еще раз.")
            await state.clear()
            return
        
        # Создаем новую запись в таблице Dialog
        dialog = Dialog.create(
            user_id=user_id,
            admin_id=selected_admin_id,
            question=question_text,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_closed=False
        )
        log_info(logger, "Новый диалог создан", {"dialog_id": dialog.id, "user_id": user_id, "admin_id": selected_admin_id})

        # Уведомляем администратора
        admin = Admin.get_or_none(Admin.user_id == selected_admin_id)
        if admin:
            try:
                reply_markup = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="Ответить", callback_data=f"reply_to_question_{dialog.id}")],
                    [InlineKeyboardButton(text="Закрыть диалог", callback_data=f"close_dialog_{dialog.id}")]
                ])
                if message.bot:
                    await message.bot.send_message(
                        chat_id=admin.user_id,
                        text=f"Новый вопрос от пользователя {message.from_user.full_name} (@{message.from_user.username or 'N/A'}):\n\n{question_text}",
                        reply_markup=reply_markup
                    )
                    log_info(logger, "Администратор уведомлен о новом вопросе", {"admin_id": admin.user_id, "dialog_id": dialog.id})
                else:
                    log_warning(logger, "Бот объект недоступен для отправки сообщения администратору.", {"admin_id": admin.user_id})
                    dialog.is_closed = True # Временное решение, чтобы диалог не висел открытым
                    dialog.save()
                    await message.answer("Ваш вопрос отправлен, но возникла проблема с уведомлением администратора. Мы постараемся ответить как можно скорее.")
                    await state.clear()
                    return
            except Exception as e:
                log_error(logger, e, f"Не удалось уведомить администратора {admin.user_id} о новом вопросе. User ID: {user_id}, Question: {question_text[:50]}...")
                # Если не удалось уведомить администратора, можно удалить диалог или пометить его как требующий внимания
                dialog.is_closed = True # Временное решение, чтобы диалог не висел открытым
                dialog.save()
                await message.answer("Ваш вопрос отправлен, но возникла проблема с уведомлением администратора. Мы постараемся ответить как можно скорее.")
                await state.clear()
                return
        else:
            log_warning(logger, "Администратор для уведомления не найден", {"selected_admin_id": selected_admin_id})
            await message.answer("Ваш вопрос отправлен, но администратор не найден. Пожалуйста, подождите ответа.")
            await state.clear()
            return

        await message.answer("Ваш вопрос отправлен администратору. Ожидайте ответа!")
        await state.clear()
    except Exception as e:
        log_error(logger, e, "Ошибка в обработчике process_user_question")
        await message.answer("Произошла ошибка при отправке вопроса. Пожалуйста, попробуйте позже.")

@router.callback_query(F.data.startswith("reply_to_question_"))
async def reply_to_question(callback: CallbackQuery, state: FSMContext) -> None:
    if not callback.data or not callback.message or isinstance(callback.message, InaccessibleMessage):
        await callback.answer()
        return

    try:
        dialog_id = int(callback.data.split("_")[-1])
        dialog = Dialog.get_or_none(Dialog.id == dialog_id)
        
        if not dialog:
            await callback.answer("❌ Диалог не найден", show_alert=True)
            return

        if dialog.is_closed:
            await callback.answer("❌ Этот диалог уже закрыт", show_alert=True)
            return

        # Сохраняем ID диалога в состояние
        await state.set_state(AskQuestionState.input_answer)
        await state.update_data(dialog_id=dialog_id)

        # Отправляем сообщение с просьбой ввести ответ
        message_obj = cast(Message, callback.message)
        await message_obj.edit_text(
            f"{message_obj.text}\n\n"
            f"✍️ Введите ваш ответ:"
        )
        await callback.answer()
    except (ValueError, IndexError) as e:
        await callback.answer("❌ Ошибка при обработке ID диалога", show_alert=True)
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)

@router.message(AskQuestionState.input_answer)
async def process_admin_answer(message: Message, state: FSMContext):
    if not message.text or not message.bot:
        await message.answer("Пожалуйста, введите ответ.")
        return

    data = await state.get_data()
    dialog_id = data.get("dialog_id")
    
    if not dialog_id:
        await message.answer("❌ Ошибка: не удалось определить диалог")
        await state.clear()
        return

    dialog = Dialog.get_or_none(Dialog.id == dialog_id)
    if not dialog:
        await message.answer("❌ Диалог не найден")
        await state.clear()
        return

    if dialog.is_closed:
        await message.answer("❌ Этот диалог уже закрыт")
        await state.clear()
        return

    # Обновляем диалог
    dialog.answer = message.text
    dialog.save()

    # Отправляем ответ пользователю
    try:
        response_message = (
            f"📬 *Ответ на ваш вопрос:*\n\n"
            f"{message.text}\n\n"
            f"💬 Вы можете продолжить диалог, просто написав новое сообщение."
        )
        await message.bot.send_message(dialog.user_id, response_message, parse_mode="Markdown")
        await message.answer("✅ Ответ успешно отправлен пользователю!")
    except Exception as e:
        await message.answer(f"❌ Ошибка при отправке ответа: {str(e)}")
    finally:
        await state.clear()

@router.callback_query(F.data.startswith("close_dialog_"))
async def close_dialog(callback: CallbackQuery):
    if not callback.data or not callback.message or isinstance(callback.message, InaccessibleMessage) or not callback.bot:
        await callback.answer()
        return

    try:
        dialog_id = int(callback.data.split("_")[-1])
        dialog = Dialog.get_or_none(Dialog.id == dialog_id)
        
        if not dialog:
            await callback.answer("❌ Диалог не найден", show_alert=True)
            return

        if dialog.is_closed:
            await callback.answer("❌ Этот диалог уже закрыт", show_alert=True)
            return

        # Закрываем диалог
        dialog.is_closed = True
        dialog.save()

        # Уведомляем пользователя
        try:
            await callback.bot.send_message(
                dialog.user_id,
                "🔒 Диалог закрыт администратором.\n"
                "Если у вас есть новые вопросы, создайте новый диалог."
            )
        except Exception:
            pass  # Игнорируем ошибку, если не удалось отправить уведомление

        message_obj = cast(Message, callback.message)
        await message_obj.edit_text(
            f"{message_obj.text}\n\n"
            f"🔒 Диалог закрыт"
        )
        await callback.answer("✅ Диалог успешно закрыт")
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)

# Обработчик для продолжения диалога
@router.message(lambda message: not message.text.startswith('/'))
async def continue_dialog(message: Message):
    if not message.from_user or not message.bot:
        return

    # Ищем активный диалог пользователя
    dialog = Dialog.get_or_none(
        (Dialog.user_id == message.from_user.id) & 
        (Dialog.is_closed == False)
    )

    if not dialog:
        return  # Если нет активного диалога, игнорируем сообщение

    # Получаем администратора
    admin = Admin.get_or_none(Admin.user_id == dialog.admin_id)
    if not admin:
        return

    # Создаем клавиатуру с кнопкой ответа
    reply_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✍️ Ответить", callback_data=f"reply_to_question_{dialog.id}")],
            [InlineKeyboardButton(text="❌ Закрыть диалог", callback_data=f"close_dialog_{dialog.id}")]
        ]
    )

    # Отправляем сообщение администратору
    try:
        await message.bot.send_message(
            admin.user_id,
            f"💬 *Новое сообщение в диалоге #{dialog.id}*\n\n"
            f"*От:* {message.from_user.full_name} (ID: `{message.from_user.id}`)\n"
            f"*Сообщение:* {message.text}",
            parse_mode="Markdown",
            reply_markup=reply_kb
        )
        await message.answer("✅ Ваше сообщение отправлено администратору!")
    except Exception as e:
        await message.answer(f"❌ Ошибка при отправке сообщения: {str(e)}")

# Новый обработчик для кнопки "Техподдержка"
@router.callback_query(F.data == "contact_tech_support")
async def contact_tech_support(callback: CallbackQuery, state: FSMContext):
    try:
        if not callback.message or isinstance(callback.message, InaccessibleMessage):
            log_warning(logger, "Получен недоступный callback message в contact_tech_support")
            await callback.answer()
            return
            
        user_id = callback.from_user.id
        tech_support_id = 5069224643  # Захардкоженный ID техподдержки
        
        log_debug(logger, "Запрос на связь с техподдержкой", {"user_id": user_id})

        # Проверяем, есть ли уже открытый диалог с техподдержкой
        existing_dialog = Dialog.get_or_none(
            (Dialog.user_id == user_id) & 
            (Dialog.admin_id == tech_support_id) & 
            (Dialog.is_closed == False)
        )

        if existing_dialog:
            log_info(logger, "У пользователя уже есть открытый диалог с техподдержкой", {"user_id": user_id, "dialog_id": existing_dialog.id})
            message_obj = cast(Message, callback.message)
            await message_obj.answer("У вас уже есть открытый диалог с техподдержкой. Пожалуйста, дождитесь ответа.")
            await callback.answer()
            return
        
        # Создаем новую запись в таблице Dialog
        dialog = Dialog.create(
            user_id=user_id,
            admin_id=tech_support_id,
            question="Пользователь запросил связь с техподдержкой.", # Начальное сообщение
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_closed=False
        )
        log_info(logger, "Новый диалог с техподдержкой создан", {"dialog_id": dialog.id, "user_id": user_id, "admin_id": tech_support_id})

        # Уведомляем техподдержку
        try:
            reply_markup = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Ответить", callback_data=f"reply_to_question_{dialog.id}")],
                [InlineKeyboardButton(text="Закрыть диалог", callback_data=f"close_dialog_{dialog.id}")]
            ])
            if callback.bot:
                await callback.bot.send_message(
                    chat_id=tech_support_id,
                    text=f"Пользователь {callback.from_user.full_name} (@{callback.from_user.username or 'N/A'}) запросил связь с техподдержкой.\n\nID пользователя: {user_id}",
                    reply_markup=reply_markup
                )
                log_info(logger, "Техподдержка уведомлена о запросе", {"admin_id": tech_support_id, "dialog_id": dialog.id})
            else:
                log_warning(logger, "Бот объект недоступен для отправки сообщения техподдержке.", {"tech_support_id": tech_support_id})
                dialog.is_closed = True # Временное решение
                dialog.save()
                message_obj = cast(Message, callback.message)
                await message_obj.answer("Произошла ошибка при связи с техподдержкой. Мы постараемся ответить как можно скорее.")
                await callback.answer()
                return
        except Exception as e:
            log_error(logger, e, f"Не удалось уведомить техподдержку {tech_support_id} о запросе. User ID: {user_id}")
            # Если не удалось уведомить техподдержку, можно удалить диалог или пометить его как требующий внимания
            dialog.is_closed = True # Временное решение
            dialog.save()
            message_obj = cast(Message, callback.message)
            await message_obj.answer("Произошла ошибка при связи с техподдержкой. Мы постараемся ответить как можно скорее.")
            await callback.answer()
            return

        message_obj = cast(Message, callback.message)
        await message_obj.answer("Мы уведомили техподдержку о вашем запросе. Ожидайте ответа!")
        await callback.answer()
    except Exception as e:
        log_error(logger, e, "Ошибка в обработчике contact_tech_support")
        if callback.message and not isinstance(callback.message, InaccessibleMessage):
            message_obj = cast(Message, callback.message)
            await message_obj.answer("Произошла ошибка при попытке связаться с техподдержкой. Пожалуйста, попробуйте позже.")
        await callback.answer()