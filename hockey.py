import time
import requests
from threading import Thread
from http.server import BaseHTTPRequestHandler, HTTPServer

TELEGRAM_TOKEN = "8423957705:AAEMRP72DHn5x0sFtswYMycB0VWUly5ZR7E"
TELEGRAM_CHAT_ID = "546949841"

# 100% открытый шлюз времени для железного теста связи
API_URL = "http://worldtimeapi.org"

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Мгновенный ответ серверу Render, чтобы он не блокировал нам интернет
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")

def run_health_server():
    # Сервер жестко держит порт 10000 в главном потоке
    server = HTTPServer(("0.0.0.0", 10000), HealthCheckHandler)
    server.serve_forever()

def send_telegram_alert(message):
    url = f"https://telegram.org{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        res = requests.post(url, json=payload, timeout=5)
        print(f"Статус отправки в ТГ: {res.status_code}")
    except Exception as e:
        print(f"Ошибка ТГ: {e}")

def time_monitoring_loop():
    """Этот цикл работает в параллельном потоке и не вешает сервер Render"""
    print("Параллельный цикл мониторинга успешно запущен...")
    # Делаем паузу 10 секунд на старте, чтобы Render успел зафиксировать запуск веб-сервера
    time.sleep(10)
    
    while True:
        try:
            response = requests.get(API_URL, timeout=5)
            if response.status_code == 200:
                current_time = response.json().get("datetime", "Unknown")
                msg = (
                    f"⏰ *ТЕСТ СВЯЗИ ПРОЙДЕН УСПЕШНО!*\n"
                    f"Сервер Render полностью живой!\n"
                    f"Точное время: {current_time}\n"
                    f"🚀 Цепочка связи Рендер -> Айфон монолитна!"
                )
                send_telegram_alert(msg)
        except Exception as e:
            print(f"Ошибка запроса времени: {e}")
        
        # Опрашиваем каждые 10 секунд
        time.sleep(10)

if __name__ == "__main__":
    print("Старт тестовой системы...")
    # 1. Запускаем бесконечный цикл опроса времени в отдельном фоновом потоке
    Thread(target=time_monitoring_loop, daemon=True).start()
    # 2. Запускаем веб-сервер в главном потоке (он будет держать порт 10000 открытым всегда)
    run_health_server()
