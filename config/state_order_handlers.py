from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram import Router, F
from data.models import Order, Books, OrderStatus
from config.logger_config import setup_logger, log_error, log_info, log_debug, log_warning
from typing import Optional, cast, Dict, Any

# Настройка логгера
logger = setup_logger('state_order_handlers')

router = Router()

class UserOrderState(StatesGroup):
    waiting_for_fio = State()
    waiting_for_address = State()
    waiting_for_phone = State()
    waiting_for_confirmation = State()

class AskQuestionState(StatesGroup):
    choose_admin = State()
    input_question = State()
    input_answer = State()

@router.callback_query(F.data.startswith("order_book_"))
async def order_book(callback: CallbackQuery, state: FSMContext):
    if not callback.data:
        await callback.answer()
        return
        
    # Получаем ID книги из callback_data
    try:
        book_id = int(callback.data.split("_")[-1])
    except (ValueError, IndexError):
        if callback.message and isinstance(callback.message, Message):
            await callback.message.answer("Ошибка при обработке заказа")
        await callback.answer()
        return
    
    # Получаем информацию о книге
    book = Books.get_or_none(Books.id == book_id)
    if not book:
        if callback.message and isinstance(callback.message, Message):
            await callback.message.answer("Книга не найдена")
        await callback.answer()
        return
    
    # Сохраняем информацию о книге в состояние
    await state.update_data(
        book_id_from_fsm=book.id,
        book_info=f"{book.name} - {book.author}"
    )
    
    # Переходим к следующему шагу
    await state.set_state(UserOrderState.waiting_for_fio)
    if callback.message and isinstance(callback.message, Message):
        await callback.message.answer("Введите ваше ФИО:")
    await callback.answer()

@router.message(UserOrderState.waiting_for_fio)
async def process_name(message:Message, state:FSMContext):
    fio = message.text
    if not fio:
        await message.reply(text="Пожалуйста, введите ваши ФИО.")
        return
    await state.update_data(fio = message.text)
    await state.set_state(UserOrderState.waiting_for_address)
    await message.answer(text="Пожалуйста, введите адрес доставки.")

@router.message(UserOrderState.waiting_for_address)
async def addres_state(message:Message, state:FSMContext):
    addres = message.text
    if not addres:
        await message.reply(text="Пожалуйста, введите адрес доставки.")
        return
    await state.update_data(addres = message.text)
    await state.set_state(UserOrderState.waiting_for_phone)
    await message.answer(text="Введите ваш номер телефона, для возможности связаться с вами.")

@router.message(UserOrderState.waiting_for_phone)
async def phone_state(message:Message, state:FSMContext):
    phone = message.text
    if not phone:
        await message.reply(text="Введите ваш номер телефона")
        return
    await state.update_data(phone = message.text)
    
    # Получаем все данные из состояния
    data = await state.get_data()
    
    if not message.from_user:
        await message.answer("Ошибка: не удалось получить ID пользователя")
        return
    
    user_id = message.from_user.id
    
    # Создаем заказ в базе данных
    Order.create(
        telegram_id=user_id,
        fio=data['fio'],
        addres=data['addres'],
        phone=data['phone'],
        book_id=data['book_id_from_fsm'],
        book_info=data['book_info']
    )
    
    await message.answer("Спасибо за заказ! Мы свяжемся с вами в ближайшее время.")
    await state.clear()

@router.message(cast(State, UserOrderState.waiting_for_fio))
async def process_fio(message: Message, state: FSMContext):
    try:
        if not message.from_user:
            log_warning(logger, "Получено сообщение без информации о пользователе")
            return
            
        log_debug(logger, "Обработка ФИО", {"user_id": message.from_user.id})
        
        # Проверяем, что сообщение содержит только текст
        if not message.text:
            log_warning(logger, "Получено не текстовое сообщение", {"user_id": message.from_user.id})
            await message.answer("Пожалуйста, введите ФИО текстом.")
            return

        # Сохраняем ФИО
        await state.update_data(fio=message.text)
        log_debug(logger, "ФИО сохранено", {"user_id": message.from_user.id, "fio": message.text})

        # Запрашиваем адрес
        await message.answer("Введите адрес доставки:")
        await state.set_state(cast(State, UserOrderState.waiting_for_address))
    except Exception as e:
        log_error(logger, e, "Ошибка при обработке ФИО")
        await message.answer("Произошла ошибка. Пожалуйста, попробуйте еще раз.")

@router.message(cast(State, UserOrderState.waiting_for_address))
async def process_address(message: Message, state: FSMContext):
    try:
        if not message.from_user:
            log_warning(logger, "Получено сообщение без информации о пользователе")
            return
            
        log_debug(logger, "Обработка адреса", {"user_id": message.from_user.id})
        
        # Проверяем, что сообщение содержит только текст
        if not message.text:
            log_warning(logger, "Получено не текстовое сообщение", {"user_id": message.from_user.id})
            await message.answer("Пожалуйста, введите адрес текстом.")
            return

        # Сохраняем адрес
        await state.update_data(address=message.text)
        log_debug(logger, "Адрес сохранен", {"user_id": message.from_user.id, "address": message.text})

        # Запрашиваем телефон
        await message.answer("Введите номер телефона:")
        await state.set_state(cast(State, UserOrderState.waiting_for_phone))
    except Exception as e:
        log_error(logger, e, "Ошибка при обработке адреса")
        await message.answer("Произошла ошибка. Пожалуйста, попробуйте еще раз.")

@router.message(cast(State, UserOrderState.waiting_for_phone))
async def process_phone(message: Message, state: FSMContext):
    try:
        if not message.from_user:
            log_warning(logger, "Получено сообщение без информации о пользователе")
            return
            
        log_debug(logger, "Обработка телефона", {"user_id": message.from_user.id})
        
        # Проверяем, что сообщение содержит только текст
        if not message.text:
            log_warning(logger, "Получено не текстовое сообщение", {"user_id": message.from_user.id})
            await message.answer("Пожалуйста, введите номер телефона текстом.")
            return

        # Сохраняем телефон
        await state.update_data(phone=message.text)
        log_debug(logger, "Телефон сохранен", {"user_id": message.from_user.id, "phone": message.text})

        # Получаем все данные
        data: Dict[str, Any] = await state.get_data()
        book_id: Optional[int] = data.get('book_id')
        
        if not book_id:
            log_error(logger, ValueError("Отсутствует book_id в данных состояния"), "Ошибка при получении данных заказа")
            await message.answer("Произошла ошибка. Пожалуйста, начните заказ заново.")
            await state.clear()
            return
            
        log_debug(logger, "Получены все данные заказа", {
            "user_id": message.from_user.id,
            "book_id": book_id,
            "fio": data.get('fio'),
            "address": data.get('address'),
            "phone": data.get('phone')
        })

        # Получаем информацию о книге
        book = Books.get_or_none(Books.id == book_id)
        if not book:
            log_error(logger, ValueError(f"Книга не найдена: {book_id}"), "Ошибка при получении информации о книге")
            await message.answer("Произошла ошибка. Пожалуйста, начните заказ заново.")
            await state.clear()
            return
        
        # Формируем сообщение для подтверждения
        confirmation_text = (
            f"Проверьте данные заказа:\n\n"
            f"📚 Книга: {book.name}\n"
            f"✍️ Автор: {book.author}\n"
            f"💰 Цена: {book.price} руб.\n\n"
            f"👤 ФИО: {data['fio']}\n"
            f"📍 Адрес: {data['address']}\n"
            f"📱 Телефон: {data['phone']}\n\n"
            f"Все верно?"
        )
        
        await message.answer(confirmation_text)
        await state.set_state(cast(State, UserOrderState.waiting_for_confirmation))
    except Exception as e:
        log_error(logger, e, "Ошибка при обработке телефона")
        await message.answer("Произошла ошибка. Пожалуйста, попробуйте еще раз.")

@router.message(cast(State, UserOrderState.waiting_for_confirmation))
async def process_confirmation(message: Message, state: FSMContext):
    try:
        if not message.from_user:
            log_warning(logger, "Получено сообщение без информации о пользователе")
            return
            
        log_debug(logger, "Обработка подтверждения заказа", {"user_id": message.from_user.id})
        
        # Проверяем ответ
        if message.text and message.text.lower() not in ['да', 'yes', 'верно', 'правильно']:
            log_warning(logger, "Пользователь отменил заказ", {"user_id": message.from_user.id})
            await message.answer("Заказ отменен. Начните заново.")
            await state.clear()
            return

        # Получаем данные заказа
        data: Dict[str, Any] = await state.get_data()
        book_id: Optional[int] = data.get('book_id')
        
        if not book_id:
            log_error(logger, ValueError("Отсутствует book_id в данных состояния"), "Ошибка при получении данных заказа")
            await message.answer("Произошла ошибка. Пожалуйста, начните заказ заново.")
            await state.clear()
            return
            
        log_debug(logger, "Создание заказа", {
            "user_id": message.from_user.id,
            "book_id": book_id,
            "fio": data.get('fio'),
            "address": data.get('address'),
            "phone": data.get('phone')
        })

        # Получаем книгу
        book = Books.get_or_none(Books.id == book_id)
        if not book:
            log_error(logger, ValueError(f"Книга не найдена: {book_id}"), "Ошибка при получении информации о книге")
            await message.answer("Произошла ошибка. Пожалуйста, начните заказ заново.")
            await state.clear()
            return
        
        # Получаем статус "новый"
        new_status = OrderStatus.get_or_none(OrderStatus.name == 'new')
        if not new_status:
            log_error(logger, ValueError("Статус 'new' не найден"), "Ошибка при получении статуса заказа")
            await message.answer("Произошла ошибка. Пожалуйста, попробуйте позже.")
            await state.clear()
            return
        
        # Создаем заказ
        order = Order.create(
            telegram_id=message.from_user.id,
            fio=data['fio'],
            addres=data['address'],
            phone=data['phone'],
            book_id=book.id,
            book_info=f"{book.name} - {book.author}",
            status=new_status
        )
        
        log_info(logger, "Заказ успешно создан", {"order_id": order.id})
        
        # Отправляем подтверждение
        await message.answer(
            "✅ Заказ успешно создан!\n\n"
            "Мы свяжемся с вами для подтверждения заказа.\n"
            "Статус заказа можно отслеживать в разделе 'Мои заказы'."
        )
        
        # Очищаем состояние
        await state.clear()
    except Exception as e:
        log_error(logger, e, "Ошибка при создании заказа")
        await message.answer("Произошла ошибка при создании заказа. Пожалуйста, попробуйте позже.")
        await state.clear()
