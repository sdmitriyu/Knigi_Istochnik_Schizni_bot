from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from data.models import Book, Order, Greeting, Admin
from config.static import commands
from config.keyboards import orders_kb, books_kb, greetings_kb, admins_kb
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup


admin_router = Router()
admin_router.message.filter(F.from_user.id.in_(Admin.select(Admin.user_id)))

@admin_router.message(Command("start"))
async def start(message: Message):
    await message.answer("Это административное меню. Выбери действие:", reply_markup=commands)

class OrderState(StatesGroup):
    name = State()
    phone = State()
    address = State()
    books = State()

class BookState(StatesGroup):
    name = State()
    author = State()
    price = State()
    description = State()
    photo = State()

class GreetingState(StatesGroup):
    message = State()

class AdminState(StatesGroup):
    username = State()

@admin_router.message(Command("add_book"))
async def add_book(message: Message, state: FSMContext):
    await state.set_state(BookState.name)
    await message.answer("Введите название книги:")

@admin_router.message(BookState.name)   
async def process_book_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(BookState.author)
    await message.answer("Введите автора книги:")

@admin_router.message(BookState.author) 
async def process_book_author(message: Message, state: FSMContext):
    await state.update_data(author=message.text)
    await state.set_state(BookState.price)
    await message.answer("Введите цену книги:")

@admin_router.message(BookState.price)  
async def process_book_price(message: Message, state: FSMContext):
    await state.update_data(price=message.text)
    await state.set_state(BookState.description)
    await message.answer("Введите описание книги:")

@admin_router.message(BookState.description)    
async def process_book_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(BookState.photo)
    await message.answer("Отправьте фото книги:")

@admin_router.message(BookState.photo)  
async def process_book_photo(message: Message, state: FSMContext):
    await state.update_data(photo=message.photo[-1].file_id)
    await state.set_state(BookState.quantity)
    await message.answer("Введите количество книг:")

@admin_router.message(BookState.quantity)   
async def process_book_quantity(message: Message, state: FSMContext):
    await state.update_data(quantity=message.text)
    await state.set_state(BookState.save)
    await message.answer("Книга добавлена в базу данных. Чтобы добавить еще одну книгу, введите команду /add_book. Чтобы вернуться в главное меню, введите команду /start.")

@admin_router.message(BookState.save)   
async def save_book(message: Message, state: FSMContext):
    data = await state.get_data()
    book = Book(
        name=data["name"],
        author=data["author"],
        price=data["price"],
        description=data["description"],
        photo=data["photo"],
        quantity=data["quantity"]
    )
    book.save() 
    await state.clear()
    await message.answer("Книга добавлена в базу данных. Чтобы добавить еще одну книгу, введите команду /add_book. Чтобы вернуться в главное меню, введите команду /start.")    


