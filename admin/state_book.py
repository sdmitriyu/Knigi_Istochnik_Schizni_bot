from aiogram.fsm.state import State, StatesGroup

class BookState(StatesGroup):
    name = State()
    author = State()
    description = State()
    price = State()
    quantity = State()
    photo = State()

class OrderState(StatesGroup):
    telegram_id = State()
    fio = State()
    addres = State()
    phone = State()
    order_complete = State()

class OrderAdminState(StatesGroup):
    selecting_order = State()
    entering_new_status = State()

class GalleryTextState(StatesGroup):
    text = State()

class OrderPretextState(StatesGroup):
    text = State()

class GreetingTextState(StatesGroup):
    text = State()

class BookEditState(StatesGroup):
    book_id = State()
    edit_field = State()
    new_name = State()
    new_author = State()
    new_description = State()
    new_price = State()
    new_quantity = State()
    new_photo = State()

class AdminEditState(StatesGroup):
    user_id = State()
    edit_field = State()
    new_user_name = State()
    new_phone = State()
 

    
