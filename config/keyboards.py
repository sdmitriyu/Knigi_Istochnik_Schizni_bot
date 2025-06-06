from aiogram import Router, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, ReplyKeyboardMarkup, KeyboardButton
from data.models import Admin

admin_router = Router()
admin_router.message.filter(F.from_user.id.in_(Admin.select(Admin.user_id)))

orders_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Добавить заказ")],
    [KeyboardButton(text="Редактировать заказ")],
    [KeyboardButton(text="Удалить заказ")],
])

books_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Добавить книгу")],
    [KeyboardButton(text="Редактировать книгу")],
    [KeyboardButton(text="Удалить книгу")],
])

greetings_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Добавить приветствие")],
    [KeyboardButton(text="Редактировать приветствие")],
    [KeyboardButton(text="Удалить приветствие")],
])

admins_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Добавить администратора")],
    [KeyboardButton(text="Редактировать администратора")],
    [KeyboardButton(text="Удалить администратора")],
])









