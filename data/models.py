from peewee import Model, SqliteDatabase, CharField, DecimalField, IntegerField, DateTimeField, TextField, SQL, FloatField, ForeignKeyField
from datetime import datetime

# Создаем прямое соединение с базой данных (без указания имени файла здесь)
db = SqliteDatabase(None, check_same_thread=False)

class BaseModel(Model):
    class Meta:
        database = db

class Books(BaseModel):
    id = IntegerField(primary_key=True)
    name = CharField()
    author = CharField()
    price = FloatField()
    description = TextField()
    photo = CharField()
    quantity = IntegerField()

class OrderStatus(BaseModel):
    name = CharField(unique=True)  # Название статуса
    description = TextField()  # Описание для внутреннего использования
    client_message = TextField()  # Сообщение для клиента
    emoji = CharField()  # Эмодзи для статуса

    class Meta:
        table_name = 'order_statuses'

    @classmethod
    def get_default_statuses(cls):
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

    def save(self, *args, **kwargs):
        self.updated_at = datetime.now()
        return super(Order, self).save(*args, **kwargs)

class Greeting(BaseModel):
    text = TextField()

class GalleryText(BaseModel):
    text = TextField()

class OrderPretext(BaseModel):
    text = TextField()

class Admin(BaseModel):
    user_id = IntegerField(unique=True)
    user_name = CharField()
    phone = CharField()

def initialize_db():
    """Инициализация базы данных"""
    # db.connect()
    db.create_tables([Books, Order, Greeting, Admin, GalleryText, OrderPretext, OrderStatus], safe=True)
    # db.close()

# Инициализируем базу данных при импорте модуля
