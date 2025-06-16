from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, ReplyKeyboardMarkup, KeyboardButton
from data.models import Books


# Основные клавиатуры
commands = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📚 Управление книгами")],
        [KeyboardButton(text="📦 Управление заказами")],
        [KeyboardButton(text="👥 Управление администраторами")],
        [KeyboardButton(text="📝 Управление текстами")],
        [KeyboardButton(text="👋 Приветствие")],
    ],
    resize_keyboard=True
)

# Клавиатуры для админ-панели (переименованы и изменены для подменю)
orders_menu_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🆕 Новые заказы")],
        [KeyboardButton(text="📋 Все заказы")],
        [KeyboardButton(text="🔄 Изменить статус заказа")],
        [KeyboardButton(text="❌ Отмена")],
        [KeyboardButton(text="🏠 Назад в главное меню")]
    ],
    resize_keyboard=True
)

books_menu_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Добавить книгу")],
        # [KeyboardButton(text="🗑 Удалить книгу")], # Удалено, так как теперь есть инлайн-кнопки
        [KeyboardButton(text="📚 Показать книги")],
        [KeyboardButton(text="❌ Отмена")],
        [KeyboardButton(text="🏠 Назад в главное меню")]
    ],
    resize_keyboard=True
)

texts_menu_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🖼 Изменить текст галереи")],
        [KeyboardButton(text="📝 Изменить текст заказа")],
        [KeyboardButton(text="👋 Изменить приветствие")],
        [KeyboardButton(text="🏠 Назад в главное меню")]
    ],
    resize_keyboard=True
)

admins_menu_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Добавить администратора")],
        # [KeyboardButton(text="🗑 Удалить администратора")], # Удалено, так как теперь есть инлайн-кнопки
        [KeyboardButton(text="👥 Список администраторов")],
        [KeyboardButton(text="🏠 Назад в главное меню")]
    ],
    resize_keyboard=True
)

greetings_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="📚 Перейти к галерее книг", callback_data="books_gallery"), 
         InlineKeyboardButton(text="📞 Связаться с поставщиком", callback_data="link_in_supplier")],
    ]
)


