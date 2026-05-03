import requests

# ТВОИ ДАННЫЕ - ВСТАВЬ ИХ СЮДА
CLIENT_ID = "R91SLJTUU2ICK85ASGB421VHH716I6G5IODTUK7RA6AFRPH8EGA41KJDMED70VHA"
CLIENT_SECRET = "J9R1GESPB1VTGRUIIV0OFG38COL5FJO3N23MUR7AO1KCK8LVVDR18F4UP7UMPQQO"

print("Получение токена...")

# Отправляем запрос к hh.ru
response = requests.post("https://hh.ru/oauth/token", data={
    "grant_type": "client_credentials",
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET
})

# Проверяем результат
if response.status_code == 200:
    data = response.json()
    token = data.get('access_token')
    print(f"\n Токен успешно получен!")
    print(f" Access Token: {token}")
    print(f" Тип: {data.get('token_type')}")

    # Сохраняем токен в файл
    with open('token.txt', 'w') as f:
        f.write(token)
    print(f"\n Токен сохранен в файл token.txt")

else:
    print(f" Ошибка: {response.status_code}")
    print(f"Текст ошибки: {response.text}")