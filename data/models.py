from peewee import Model, SqliteDatabase, CharField, DecimalField, IntegerField, DateTimeField, TextField, SQL

db = SqliteDatabase('data/books.db')

class BaseModel(Model):
    class Meta:
        database = db

class Book(BaseModel):
    photo = TextField()  # file_id из Telegram
    name = CharField()
    author = CharField()
    description = TextField(default=None)
    price = DecimalField(max_digits=10, decimal_places=2)
    quantity = IntegerField(default=0)
    created_at = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')])

class Order(BaseModel):
    full_name = CharField()
    address = TextField()
    phone = CharField()
    books = TextField()  # JSON-строка с id и количеством книг
    created_at = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')])

class Greeting(BaseModel):
    message = TextField()
    updated_at = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')])

class Admin(BaseModel):
    user_id = IntegerField(unique=True)
