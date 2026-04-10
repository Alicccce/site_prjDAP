from DataBase import engine, User
from sqlalchemy.orm import sessionmaker

SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()

users = session.query(User).all()

print("")
print("ЗАРЕГИСТРИРОВАННЫЕ ПОЛЬЗОВАТЕЛИ\n")
if not users:
    print("Пользователей пока нет")
else:
    for user in users:
        print(f"ID: {user.id}")
        print(f"Email: {user.email}")
        print(f"Имя: {user.name}")
        print(f"Дата регистрации: {user.registration_date}")
        print("-" * 50)

session.close()