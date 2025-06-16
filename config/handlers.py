from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, InaccessibleMessage
from aiogram.filters import Command
from data.models import Greeting, Admin
from config.keyboards import greetings_kb
from data.models import Books


router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    # Check if the user is an admin. If so, let the admin_router handle it.
    if message.from_user and Admin.get_or_none(Admin.user_id == message.from_user.id):
        return # Do not send a keyboard if the user is an admin

    great = Greeting.get_or_none()
    if great:
        await message.answer(great.text, reply_markup=greetings_kb)
    else:
        await message.answer("Добро пожаловать!", reply_markup=greetings_kb)

@router.message(Command("help"))
async def help(message: Message):
    await message.answer("Help")

@router.callback_query(F.data == "books_gallery")
async def go_in_gallery(callback: CallbackQuery):
    books = Books.select()
    if not books:
        if callback.message and isinstance(callback.message, Message) and not isinstance(callback.message, InaccessibleMessage):
            await callback.message.answer(text="В базе нет книг.")
        await callback.answer()
        return
    
    pregallery_text = "Вы перешли в галерею книг."
    for book in books:
        pregallery_text += (
            f"Название: {book.name}\n"
            f"Автор: {book.author}\n"
            f"Цена: {book.price} руб.\n"
            f"Количество: {book.quantity} шт.\n"
            f"Описание: {book.description}\n\n"
        )
        # Создаем кнопку для каждой книги с её ID
        order_kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=f"Заказать {book.name}", callback_data=f"order_book_{book.id}")]
            ]
        )
        if callback.message and isinstance(callback.message, Message) and not isinstance(callback.message, InaccessibleMessage):
            await callback.message.answer(pregallery_text, reply_markup=order_kb)
    await callback.answer()

@router.callback_query(F.data.startswith("order_book_"))
async def process_order(callback: CallbackQuery):
    if not callback.data:
        await callback.answer()
        return
        
    # Получаем ID книги из callback_data
    try:
        book_id = int(callback.data.split("_")[-1])
    except (ValueError, IndexError):
        if callback.message and isinstance(callback.message, Message) and not isinstance(callback.message, InaccessibleMessage):
            await callback.message.answer("Ошибка при обработке заказа")
        await callback.answer()
        return
    
    # Получаем информацию о книге
    book = Books.get_or_none(Books.id == book_id)
    if not book:
        if callback.message and isinstance(callback.message, Message) and not isinstance(callback.message, InaccessibleMessage):
            await callback.message.answer("Книга не найдена")
        await callback.answer()
        return
    
    # Здесь можно добавить логику оформления заказа
    if callback.message and isinstance(callback.message, Message) and not isinstance(callback.message, InaccessibleMessage):
        await callback.message.answer(
            f"Вы выбрали книгу:\n"
            f"Название: {book.name}\n"
            f"Автор: {book.author}\n"
            f"Цена: {book.price} руб.\n\n"
            f"Для оформления заказа введите свои данные в формате:\n"
            f"ФИО, адрес, телефон"
        )
    await callback.answer()

@router.callback_query(F.data == "contact_admin")
async def contact_admin(callback: CallbackQuery):
    # Получаем первого администратора из базы данных
    admin = Admin.get_or_none()
    if not admin:
        if callback.message and isinstance(callback.message, Message) and not isinstance(callback.message, InaccessibleMessage):
            await callback.message.answer("К сожалению, администратор недоступен.")
        await callback.answer()
        return
    
    response_text = ""
    if admin.user_name:
        admin_link = f"https://t.me/{admin.user_name}"
        response_text += (
            f"Для связи с администратором перейдите по ссылке: {admin_link}\n"
            f"Или напишите напрямую: @{admin.user_name}\n"
        )
    
    if admin.phone:
        response_text += f"Номер телефона администратора: +{admin.phone}\n"
    
    if not response_text:
        response_text = "К сожалению, контактная информация администратора не указана."

    if isinstance(callback.message, Message) and not isinstance(callback.message, InaccessibleMessage):
        await callback.message.answer(response_text)
        await callback.answer()
    else:
        await callback.answer(response_text, show_alert=True)