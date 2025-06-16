from aiogram.fsm.context import FSMContext
from data.models import Order, Books, db
from admin.state_book import OrderState
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message

router = Router()

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
    await state.set_state(OrderState.fio)
    if callback.message and isinstance(callback.message, Message):
        await callback.message.answer("Введите ваше ФИО:")
    await callback.answer()

@router.message(OrderState.fio)
async def process_name(message:Message, state:FSMContext):
    fio = message.text
    if not fio:
        await message.reply(text="Пожалуйста, введите ваши ФИО.")
        return
    await state.update_data(fio = message.text)
    await state.set_state(OrderState.addres)
    await message.answer(text="Пожалуйста, введите адрес доставки.")

@router.message(OrderState.addres)
async def addres_state(message:Message, state:FSMContext):
    addres = message.text
    if not addres:
        await message.reply(text="Пожалуйста, введите адрес доставки.")
        return
    await state.update_data(addres = message.text)
    await state.set_state(OrderState.phone)
    await message.answer(text="Введите ваш номер телефона, для возможности связаться с вами.")

@router.message(OrderState.phone)
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
