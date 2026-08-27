import time
import requests
from threading import Thread
from http.server import BaseHTTPRequestHandler, HTTPServer

TELEGRAM_TOKEN = "8423957705:AAEMRP72DHn5x0sFtswYMycB0VWUly5ZR7E"
TELEGRAM_CHAT_ID = "546949841"

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")

def run_health_server():
    server = HTTPServer(("0.0.0.0", 10000), HealthCheckHandler)
    server.serve_forever()

def check_telegram_connection():
    """Жесткая проверка шлюза Telegram с выводом ответа сервера в логи"""
    print("--- ЗАПУСК ДИАГНОСТИКИ ШЛЮЗА TELEGRAM ---")
    time.sleep(5)
    
    url = f"https://telegram.org{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID, 
        "text": "🚨 ТЕСТ КАНАЛА СВЯЗИ: РЕНДЕР ПРОБИВАЕТ ЭКРАН!"
    }
    
    try:
        print(f"Отправка запроса на сервер Telegram...")
        response = requests.post(url, json=payload, timeout=10)
        print(f"1. Код ответа от серверов Telegram: {response.status_code}")
        print(f"2. Текст ответа от серверов Telegram: {response.text}")
    except Exception as e:
        print(f"❌ КРИТИЧЕСКАЯ ОШИБКА ИСПРАВНОСТИ СЕТИ: {e}")

if __name__ == "__main__":
    # Запускаем диагностику один раз при старте в фоновом режиме
    Thread(target=check_telegram_connection, daemon=True).start()
    run_health_server()
