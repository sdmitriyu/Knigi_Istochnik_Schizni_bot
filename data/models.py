from peewee import Model, SqliteDatabase, CharField, DecimalField, IntegerField, DateTimeField, TextField, SQL, FloatField, ForeignKeyField, BooleanField
from datetime import datetime
from typing import Optional, List, Dict, Any, Union, TypeVar, Generic
import logging
import traceback

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Создаем прямое соединение с базой данных (без указания имени файла здесь)
db = SqliteDatabase(None, check_same_thread=False)

class ValidationError(Exception):
    """Кастомный класс для ошибок валидации"""
    pass

class BaseModel(Model):
    class Meta:
        database = db
        legacy_table_names = False
        table_function = lambda cls: cls.__name__.lower()

    def validate(self) -> None:
        """Базовый метод валидации"""
        logger.debug(f"Вызов базового метода валидации для {self.__class__.__name__}")

    def save(self, *args: Any, **kwargs: Any) -> bool:
        """Переопределяем метод save для добавления логирования"""
        try:
            logger.debug(f"Начало сохранения {self.__class__.__name__} с параметрами: args={args}, kwargs={kwargs}")
            self.validate()
            result = super(BaseModel, self).save(*args, **kwargs)
            logger.info(f"Успешно сохранена запись {self.__class__.__name__} с id {getattr(self, 'id', 'unknown')}")
            return result
        except Exception as e:
            logger.error(f"Ошибка при сохранении {self.__class__.__name__}: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

class Books(BaseModel):
    id = IntegerField(primary_key=True)
    name = CharField()
    author = CharField()
    price = FloatField()
    description = TextField()
    photo = CharField()
    quantity = IntegerField()

    def validate(self) -> None:
        logger.debug(f"Валидация книги: name={self.name}, author={self.author}, price={self.price}, quantity={self.quantity}")
        if not self.name:
            logger.error("Ошибка валидации: отсутствует название книги")
            raise ValidationError("Название книги обязательно")
        if not self.author:
            logger.error("Ошибка валидации: отсутствует автор книги")
            raise ValidationError("Автор книги обязателен")
        if not self.description:
            logger.error("Ошибка валидации: отсутствует описание книги")
            raise ValidationError("Описание книги обязательно")
        if not self.photo:
            logger.error("Ошибка валидации: отсутствует фото книги")
            raise ValidationError("Фото книги обязательно")

    def save(self, *args: Any, **kwargs: Any) -> bool:
        try:
            logger.debug(f"Сохранение книги: name={self.name}, author={self.author}, price={self.price}, quantity={self.quantity}")
            # Проверка на None значения
            if self.price is None:
                logger.error("Ошибка валидации: отсутствует цена книги")
                raise ValidationError("Цена обязательна")
            if self.quantity is None:
                logger.error("Ошибка валидации: отсутствует количество книг")
                raise ValidationError("Количество обязательно")
            
            return super().save(*args, **kwargs)
        except Exception as e:
            logger.error(f"Ошибка при сохранении книги: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

class OrderStatus(BaseModel):
    name = CharField(unique=True)
    description = TextField()
    client_message = TextField()
    emoji = CharField()

    def validate(self) -> None:
        logger.debug(f"Валидация статуса заказа: name={self.name}, emoji={self.emoji}")
        if not self.name:
            logger.error("Ошибка валидации: отсутствует название статуса")
            raise ValidationError("Название статуса обязательно")
        if not self.emoji:
            logger.error("Ошибка валидации: отсутствует эмодзи статуса")
            raise ValidationError("Эмодзи статуса обязательно")
        if not self.description:
            logger.error("Ошибка валидации: отсутствует описание статуса")
            raise ValidationError("Описание статуса обязательно")
        if not self.client_message:
            logger.error("Ошибка валидации: отсутствует сообщение для клиента")
            raise ValidationError("Сообщение для клиента обязательно")

    @classmethod
    def get_default_statuses(cls) -> List[Dict[str, str]]:
        logger.debug("Получение списка статусов заказа по умолчанию")
        return [
            {
                'name': 'new',
                'description': 'Новый заказ',
                'client_message': 'Ваш заказ принят и ожидает обработки.',
                'emoji': '🆕'
            },
            {
                'name': 'processing',
                'description': 'В обработке',
                'client_message': 'Ваш заказ обрабатывается.',
                'emoji': '⚙️'
            },
            {
                'name': 'supplier_notified',
                'description': 'Поставщик уведомлен',
                'client_message': 'Поставщик уведомлен о вашем заказе.',
                'emoji': '📢'
            },
            {
                'name': 'book_taken',
                'description': 'Книга забрана поставщиком',
                'client_message': 'Книга забрана поставщиком и готовится к отправке.',
                'emoji': '📦'
            },
            {
                'name': 'in_transit',
                'description': 'В пути',
                'client_message': 'Ваш заказ в пути.',
                'emoji': '🚚'
            },
            {
                'name': 'delivered',
                'description': 'Доставлен',
                'client_message': 'Ваш заказ доставлен!',
                'emoji': '✅'
            },
            {
                'name': 'cancelled',
                'description': 'Отменен',
                'client_message': 'Ваш заказ отменен.',
                'emoji': '❌'
            }
        ]

class Order(BaseModel):
    id = IntegerField(primary_key=True)
    telegram_id = IntegerField()
    fio = CharField()
    addres = CharField()
    phone = CharField()
    book_id = ForeignKeyField(Books)
    book_info = TextField()
    status = ForeignKeyField(OrderStatus, backref='orders', default='new')
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)

    def validate(self) -> None:
        logger.debug(f"Валидация заказа: telegram_id={self.telegram_id}, fio={self.fio}, phone={self.phone}")
        if not self.telegram_id:
            logger.error("Ошибка валидации: отсутствует ID пользователя Telegram")
            raise ValidationError("ID пользователя Telegram обязателен")
        if not self.fio:
            logger.error("Ошибка валидации: отсутствует ФИО")
            raise ValidationError("ФИО обязательно")
        if not self.addres:
            logger.error("Ошибка валидации: отсутствует адрес")
            raise ValidationError("Адрес обязателен")
        if not self.phone:
            logger.error("Ошибка валидации: отсутствует телефон")
            raise ValidationError("Телефон обязателен")
        if not self.book_id:
            logger.error("Ошибка валидации: отсутствует книга")
            raise ValidationError("Книга обязательна")
        if not self.book_info:
            logger.error("Ошибка валидации: отсутствует информация о книге")
            raise ValidationError("Информация о книге обязательна")
        if not self.status:
            logger.error("Ошибка валидации: отсутствует статус заказа")
            raise ValidationError("Статус заказа обязателен")

    def save(self, *args: Any, **kwargs: Any) -> bool:
        logger.debug(f"Сохранение заказа: telegram_id={self.telegram_id}, fio={self.fio}, phone={self.phone}")
        self.updated_at = datetime.now()
        return super(Order, self).save(*args, **kwargs)

class Greeting(BaseModel):
    text = TextField()

    def validate(self) -> None:
        logger.debug(f"Валидация приветствия: text={self.text[:50]}...")
        if not self.text:
            logger.error("Ошибка валидации: отсутствует текст приветствия")
            raise ValidationError("Текст приветствия обязателен")

class GalleryText(BaseModel):
    text = TextField()

    def validate(self) -> None:
        logger.debug(f"Валидация текста галереи: text={self.text[:50]}...")
        if not self.text:
            logger.error("Ошибка валидации: отсутствует текст галереи")
            raise ValidationError("Текст галереи обязателен")

class OrderPretext(BaseModel):
    text = TextField()

    def validate(self) -> None:
        logger.debug(f"Валидация текста оформления заказа: text={self.text[:50]}...")
        if not self.text:
            logger.error("Ошибка валидации: отсутствует текст оформления заказа")
            raise ValidationError("Текст оформления заказа обязателен")

class Admin(BaseModel):
    user_id = IntegerField(unique=True)
    user_name = CharField()
    phone = CharField()
    role = CharField(default='admin')
    display_name = CharField(null=True)

    def validate(self) -> None:
        logger.debug(f"Валидация администратора: user_id={self.user_id}, user_name={self.user_name}, role={self.role}")
        if not self.user_id:
            logger.error("Ошибка валидации: отсутствует ID пользователя")
            raise ValidationError("ID пользователя обязателен")
        if not self.user_name:
            logger.error("Ошибка валидации: отсутствует имя пользователя")
            raise ValidationError("Имя пользователя обязательно")
        if not self.phone:
            logger.error("Ошибка валидации: отсутствует телефон")
            raise ValidationError("Телефон обязателен")
        if not self.role:
            logger.error("Ошибка валидации: отсутствует роль")
            raise ValidationError("Роль обязательна")

class Dialog(BaseModel):
    id = IntegerField(primary_key=True)
    user_id = IntegerField()
    admin_id = IntegerField()
    question = TextField()
    answer = TextField(null=True)
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)
    is_closed = BooleanField(default=False)

    def validate(self) -> None:
        logger.debug(f"Валидация диалога: user_id={self.user_id}, admin_id={self.admin_id}, is_closed={self.is_closed}")
        if not self.user_id:
            logger.error("Ошибка валидации: отсутствует ID пользователя")
            raise ValidationError("ID пользователя обязателен")
        if not self.admin_id:
            logger.error("Ошибка валидации: отсутствует ID администратора")
            raise ValidationError("ID администратора обязателен")
        if not self.question:
            logger.error("Ошибка валидации: отсутствует вопрос")
            raise ValidationError("Вопрос обязателен")
        if self.answer is not None and not self.answer:
            logger.error("Ошибка валидации: пустой ответ")
            raise ValidationError("Ответ не может быть пустым")

    def save(self, *args: Any, **kwargs: Any) -> bool:
        logger.debug(f"Сохранение диалога: user_id={self.user_id}, admin_id={self.admin_id}, is_closed={self.is_closed}")
        self.updated_at = datetime.now()
        return super(Dialog, self).save(*args, **kwargs)
