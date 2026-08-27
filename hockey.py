import time
import requests

TELEGRAM_TOKEN = "8423957705:AAEMRP72DHn5x0sFtswYMycB0VWUly5ZR7E"
TELEGRAM_CHAT_ID = "546949841"

def check_telegram_connection():
    """Чистая отправка пуша в Telegram без всяких портов и серверов"""
    url = f"https://telegram.org{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID, 
        "text": "⏰ ПРОБОЙ СВЯЗИ! ФОНОВЫЙ РОБОТ НА RENDER НА СВЯЗИ С АЙФОНОМ!"
    }
    
    while True:
        try:
            print("Отправка тестового сигнала в Telegram...")
            response = requests.post(url, json=payload, timeout=10)
            print(f"Ответ сервера ТГ: {response.status_code}")
        except Exception as e:
            print(f"Ошибка сети: {e}")
        
        # Шлём пуш каждые 15 секунд для теста связи
        time.sleep(15)

if __name__ == "__main__":
    print("Фоновый робот успешно стартовал в облаке...")
    check_telegram_connection()
