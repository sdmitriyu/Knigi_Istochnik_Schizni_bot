import sys
import os

# Добавляем корневую директорию проекта в путь Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.models import db, Admin

def create_first_admin(user_id: int, user_name: str, phone: int):
    try:
        # Проверяем, существует ли уже администратор
        if Admin.select().exists():
            print("Администратор уже существует в базе данных!")
            return False

        # Создаем первого администратора
        Admin.create(
            user_id=user_id,
            user_name=user_name,
            phone=phone
        )
        print("Первый администратор успешно создан!")
        return True
    except Exception as e:
        print(f"Ошибка при создании администратора: {str(e)}")
        return False