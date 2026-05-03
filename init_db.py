# init_db.py (в корне site-project/)
from DataBase import User, engine, Base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

# Создаём таблицы
Base.metadata.create_all(engine)
print("Таблицы созданы/проверены")

# Создаём сессию
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

# Создаём тестового пользователя
test_email = "alex@example.com"
user = db.query(User).filter_by(email=test_email).first()

if not user:
    test_user = User(
        email=test_email,
        name="alex",
        password_hash="hash_for_testing",
        registration_date=datetime.now()
    )
    db.add(test_user)
    db.commit()
    print(f"Создан тестовый пользователь: id={test_user.id}, email={test_email}")
else:
    print(f"Пользователь уже существует: id={user.id}, email={user.email}")

# Показываем всех пользователей
all_users = db.query(User).all()
print("\nСписок пользователей в БД:")
for u in all_users:
    print(f"   - id={u.id}, email={u.email}, имя={u.name}")

db.close()