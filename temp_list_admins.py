import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))
from data.models import Admin, db

db.connect()

try:
    admins = Admin.select()
    if admins:
        print('Existing Admins:')
        for admin in admins:
            print(f'ID: {admin.user_id}, Name: {admin.user_name}, Phone: {admin.phone}')
    else:
        print('No admins found.')
finally:
    if not db.is_closed():
        db.close() 