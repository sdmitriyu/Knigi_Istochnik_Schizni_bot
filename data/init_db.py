from models import db, OrderStatus

def init_order_statuses():
    """Инициализация статусов заказов"""
    # Проверяем, есть ли уже статусы в базе
    if OrderStatus.select().count() == 0:
        # Получаем список статусов по умолчанию
        default_statuses = OrderStatus.get_default_statuses()
        
        # Создаем статусы в базе данных
        for status_data in default_statuses:
            OrderStatus.create(**status_data)
        
        print("✅ Статусы заказов успешно инициализированы")
    else:
        print("ℹ️ Статусы заказов уже существуют в базе данных")

def init_database():
    """Инициализация базы данных"""
    db.connect()
    db.create_tables([OrderStatus], safe=True)
    init_order_statuses()
    db.close()

if __name__ == "__main__":
    init_database() 