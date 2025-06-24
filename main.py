import asyncio
import os
import sys
import traceback
from typing import Any, Dict, List

# Установка кодировки UTF-8 для консоли Windows
if sys.platform == "win32":
    os.system("chcp 65001")

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
from aiogram.types import BotCommand, BotCommandScopeAllPrivateChats

from config.handlers import router
from admin.state_book_handlers import admin_router
from admin.edit_texts_handlers import admin_texts_router
from admin.edit_great import admin_great_router
from admin.rigister_admin import register_admin_router
from data.models import db, Books, Order, Greeting, Admin, GalleryText, OrderPretext, OrderStatus, Dialog
from aiogram.filters import Command
from config.keyboards import commands
from config.logger_config import setup_logger, log_error, log_info, log_debug, log_warning

# Настройка логгера
logger = setup_logger('main')

# Загрузка переменных окружения
load_dotenv(".env")
TOKEN = os.getenv("TOKEN")

if TOKEN is None:
    log_error(logger, ValueError("TOKEN environment variable not set. Please create a .env file with TOKEN=YOUR_BOT_TOKEN"))
    raise ValueError("TOKEN environment variable not set. Please create a .env file with TOKEN=YOUR_BOT_TOKEN")

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Подключение роутеров
log_debug(logger, "Подключение роутеров")
dp.include_router(admin_texts_router)
dp.include_router(admin_great_router)
dp.include_router(register_admin_router)
dp.include_router(admin_router)
dp.include_router(router)

log_debug(logger, f"Содержимое клавиатуры команд при запуске", {"keyboard": commands.keyboard})

def initialize_database_and_data():
    """Инициализация базы данных и заполнение начальными данными"""
    try:
        log_info(logger, "Начало инициализации базы данных")
        
        # Создаем таблицы
        log_debug(logger, "Создание таблиц")
        db.create_tables([
            Books, 
            Order, 
            Greeting, 
            Admin, 
            GalleryText, 
            OrderPretext, 
            OrderStatus, 
            Dialog
        ], safe=True)

        # Создаем таблицу статусов заказа с правильным именем (если необходимо)
        try:
            log_debug(logger, "Создание таблицы order_statuses")
            db.execute_sql('CREATE TABLE IF NOT EXISTS order_statuses (id INTEGER PRIMARY KEY, name VARCHAR(255) UNIQUE, description TEXT, client_message TEXT, emoji VARCHAR(255));')
        except Exception as e:
            log_warning(logger, f"Таблица order_statuses уже существует: {str(e)}")
            log_debug(logger, f"Traceback: {traceback.format_exc()}")

        # Проверяем и добавляем колонки в таблицу admin
        try:
            log_debug(logger, "Проверка и добавление колонок в таблицу admin")
            # Проверяем существование колонок
            cursor = db.execute_sql("PRAGMA table_info(admin);")
            columns = [column[1] for column in cursor.fetchall()]
            log_debug(logger, f"Существующие колонки в таблице admin: {columns}")
            
            # Добавляем колонку role если её нет
            if 'role' not in columns:
                log_info(logger, "Добавляем колонку role в таблицу admin")
                db.execute_sql('ALTER TABLE admin ADD COLUMN role VARCHAR(255) DEFAULT "admin";')
            
            # Добавляем колонку display_name если её нет
            if 'display_name' not in columns:
                log_info(logger, "Добавляем колонку display_name в таблицу admin")
                db.execute_sql('ALTER TABLE admin ADD COLUMN display_name VARCHAR(255);')
        except Exception as e:
            log_error(logger, e, "Ошибка при проверке/добавлении колонок")
            log_debug(logger, f"Traceback: {traceback.format_exc()}")

        # Инициализируем статусы заказа
        log_debug(logger, "Инициализация статусов заказа")
        for status_data in OrderStatus.get_default_statuses():
            try:
                OrderStatus.get_or_create(name=status_data['name'], defaults=status_data)
                log_debug(logger, f"Статус заказа создан/обновлен: {status_data['name']}")
            except Exception as e:
                log_error(logger, e, f"Ошибка при создании статуса {status_data['name']}")
                log_debug(logger, f"Traceback: {traceback.format_exc()}")

        # Создаем администратора по умолчанию
        try:
            log_debug(logger, "Создание администратора по умолчанию")
            Admin.get_or_create(
                user_id=5069224643,
                defaults={
                    'user_name': 'Dmitriy_hrist_muz', 
                    'phone': '0', 
                    'role': 'tech_support', 
                    'display_name': 'Дмитрий (Техподдержка)'
                }
            )
        except Exception as e:
            log_error(logger, e, "Ошибка при создании администратора по умолчанию")
            log_debug(logger, f"Traceback: {traceback.format_exc()}")
            # Пробуем создать администратора напрямую
            try:
                log_debug(logger, "Попытка прямого создания администратора")
                db.execute_sql('''
                    INSERT OR IGNORE INTO admin (user_id, user_name, phone, role, display_name)
                    VALUES (5069224643, 'Dmitriy_hrist_muz', '0', 'tech_support', 'Дмитрий (Техподдержка)');
                ''')
            except Exception as e2:
                log_error(logger, e2, "Ошибка при прямом создании администратора")
                log_debug(logger, f"Traceback: {traceback.format_exc()}")

        # Инициализируем текстовые поля
        try:
            log_debug(logger, "Инициализация текстовых полей")
            # Приветствие
            Greeting.get_or_create(
                id=1,
                defaults={'text': 'Добро пожаловать в наш книжный магазин! 📚\n\nЗдесь вы можете:\n- Просмотреть каталог книг\n- Оформить заказ\n- Связаться с администрацией\n- Получить помощь'}
            )
            log_debug(logger, "Приветствие создано/обновлено")
            
            # Текст галереи
            GalleryText.get_or_create(
                id=1,
                defaults={'text': '📚 *Наш каталог книг*\n\nВыберите книгу для просмотра подробной информации и оформления заказа.'}
            )
            log_debug(logger, "Текст галереи создан/обновлен")
            
            # Текст оформления заказа
            OrderPretext.get_or_create(
                id=1,
                defaults={'text': '📦 *Оформление заказа*\n\nДля оформления заказа, пожалуйста, заполните следующие данные:'}
            )
            log_debug(logger, "Текст оформления заказа создан/обновлен")
            
            log_info(logger, "Текстовые поля успешно инициализированы")
        except Exception as e:
            log_error(logger, e, "Ошибка при инициализации текстовых полей")
            log_debug(logger, f"Traceback: {traceback.format_exc()}")

        # Инициализируем тестовые книги
        try:
            log_debug(logger, "Инициализация тестовых книг")
            # Проверяем, есть ли уже книги в базе
            book_count = Books.select().count()
            log_debug(logger, f"Текущее количество книг в базе: {book_count}")
            
            if book_count == 0:
                test_books = [
                    {
                        'name': 'Библия',
                        'author': 'Священное Писание',
                        'price': 1000.0,
                        'description': 'Священное Писание Ветхого и Нового Завета',
                        'photo': 'bible.jpg',
                        'quantity': 10
                    },
                    {
                        'name': 'Молитвослов',
                        'author': 'Православная Церковь',
                        'price': 500.0,
                        'description': 'Сборник основных православных молитв',
                        'photo': 'prayer_book.jpg',
                        'quantity': 15
                    },
                    {
                        'name': 'Закон Божий',
                        'author': 'Протоиерей Серафим Слободской',
                        'price': 800.0,
                        'description': 'Руководство для семьи и школы',
                        'photo': 'law_of_god.jpg',
                        'quantity': 8
                    },
                    {
                        'name': 'Жития Святых',
                        'author': 'Святитель Димитрий Ростовский',
                        'price': 1200.0,
                        'description': 'Сборник житий святых угодников Божиих',
                        'photo': 'lives_of_saints.jpg',
                        'quantity': 5
                    },
                    {
                        'name': 'Псалтирь',
                        'author': 'Царь Давид',
                        'price': 600.0,
                        'description': 'Книга псалмов царя Давида',
                        'photo': 'psalter.jpg',
                        'quantity': 12
                    }
                ]
                
                for book_data in test_books:
                    try:
                        Books.create(**book_data)
                        log_debug(logger, f"Создана тестовая книга: {book_data['name']}")
                    except Exception as e:
                        log_error(logger, e, f"Ошибка при создании книги {book_data['name']}")
                        log_debug(logger, f"Traceback: {traceback.format_exc()}")
                
                log_info(logger, "Тестовые книги успешно добавлены")
        except Exception as e:
            log_error(logger, e, "Ошибка при инициализации тестовых книг")
            log_debug(logger, f"Traceback: {traceback.format_exc()}")
        
        log_info(logger, "База данных успешно инициализирована")
    except Exception as e:
        log_error(logger, e, "Ошибка при инициализации базы данных")
        log_debug(logger, f"Traceback: {traceback.format_exc()}")
        raise

async def main():
    try:
        log_info(logger, "Инициализация базы данных")
        db.init('books.db')
        db.connect()
        initialize_database_and_data() # Вызываем новую функцию инициализации
        
        # Установка списка команд для бота
        commands_for_bot = [
            BotCommand(command="start", description="Запустить бота"),
            BotCommand(command="help", description="Получить помощь")
        ]
        
        log_debug(logger, "Установка команд бота", {"commands": commands_for_bot})
        await bot.set_my_commands(commands=commands_for_bot, scope=BotCommandScopeAllPrivateChats())
        
        log_info(logger, "Запуск бота")
        await dp.start_polling(bot)
    except Exception as e:
        log_error(logger, e, "Ошибка при запуске бота")
        raise
    finally:
        if not db.is_closed():
            log_debug(logger, "Закрытие соединения с базой данных")
            db.close()

if __name__ == "__main__":
    try:
        log_info(logger, "Запуск приложения")
        asyncio.run(main())
    except Exception as e:
        log_error(logger, e, "Критическая ошибка при запуске приложения")
        raise
