import time
import requests
from threading import Thread
from http.server import BaseHTTPRequestHandler, HTTPServer

# ТВОЙ НОВЫЙ ТОЧНЫЙ ТОКЕН И ID
TELEGRAM_TOKEN = "8149255673:AAH3k_j6Zk8x8bO6N_3YtM1f8bK8m7P_L8w"
TELEGRAM_CHAT_ID = "546949841"

# Открытый шлюз времени для моментального пробоя тишины
API_URL = "http://worldtimeapi.org"

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Мгновенный ответ серверу Render, чтобы открыть интернет-шлюз
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")

def run_health_server():
    # Сервер держит порт 10000 для бесплатного тарифа Render
    server = HTTPServer(("0.0.0.0", 10000), HealthCheckHandler)
    server.serve_forever()

def send_telegram_alert(message):
    url = f"https://telegram.org{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        res = requests.post(url, json=payload, timeout=5)
        print(f"Ответ Telegram API: {res.status_code}")
    except Exception as e:
        print(f"Ошибка отправки: {e}")

def time_monitoring_loop():
    print("Параллельный поток проверки связи успешно запущен...")
    time.sleep(5)
    
    while True:
        try:
            response = requests.get(API_URL, timeout=5)
            if response.status_code == 200:
                current_time = response.json().get("datetime", "Unknown")
                msg = (
                    f"⏰ *ТЕСТ СВЯЗИ ПРОЙДЕН УСПЕШНО!*\n"
                    f"Твой новый токен полностью рабочий!\n"
                    f"Точное время на сервере: {current_time}\n"
                    f"🚀 Цепочка Render -> Бот @Qwerty1244785_bot монолитна!"
                )
                send_telegram_alert(msg)
        except Exception as e:
            print(f"Ошибка запроса времени: {e}")
        
        # Шлем пуш каждые 15 секунд для проверки связи
        time.sleep(15)

if __name__ == "__main__":
    print("Старт проверочного софта...")
    # 1. Запускаем опрос времени в отдельном потоке
    Thread(target=time_monitoring_loop, daemon=True).start()
    # 2. Удерживаем порт 10000 в главном потоке для бесплатного тарифа Render
    run_health_server()
