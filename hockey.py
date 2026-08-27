import time
import requests
from threading import Thread
from http.server import BaseHTTPRequestHandler, HTTPServer

TELEGRAM_TOKEN = "8423957705:AAEMRP72DHn5x0sFtswYMycB0VWUly5ZR7E"
TELEGRAM_CHAT_ID = "546949841"

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Жесткий и мгновенный ответ серверу Render, чтобы закрыть ошибку Port Scan Timeout
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")

def run_health_server():
    # Этот сервер вечно держит порт 10000 для бесплатного тарифа Render
    server = HTTPServer(("0.0.0.0", 10000), HealthCheckHandler)
    server.serve_forever()

def check_telegram_connection():
    """Параллельный цикл: шлет пуши в Телеграм, вообще не нагружая сервер портов"""
    url = f"https://telegram.org{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID, 
        "text": "⏰ БЕСПЛАТНЫЙ ТЕСТ ПРОЙДЕН! СВЯЗЬ РЕНДЕР -> АЙФОН ПРОБИТА!"
    }
    
    # Даем серверу Render 5 секунд спокойно зафиксировать порт при старте
    time.sleep(5)
    
    while True:
        try:
            print("Фоновый поток: отправка тестового сигнала...")
            response = requests.post(url, json=payload, timeout=10)
            print(f"Ответ Telegram API: {response.status_code}")
        except Exception as e:
            print(f"Ошибка сети: {e}")
        
        # Интервал отправки — 15 секунд
        time.sleep(15)

if __name__ == "__main__":
    print("Старт бесплатного робота-снайпера...")
    # 1. Запускаем отправку пушей в параллельном независимом потоке
    Thread(target=check_telegram_connection, daemon=True).start()
    # 2. Запускаем удержание порта 10000 в главном потоке
    run_health_server()
