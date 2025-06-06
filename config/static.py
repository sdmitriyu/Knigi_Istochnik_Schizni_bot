from aiogram.types import BotCommand

commands = [
    BotCommand(command="/help", description="Помощь"),
    BotCommand(command="/list_orders", description="Список заказов"),
    BotCommand(command="/list_books", description="Список книг"),
    BotCommand(command="/list_greetings", description="Список приветствий"),
    BotCommand(command="/list_admins", description="Список администраторов"),
]

