import time
import requests
from threading import Thread
from http.server import BaseHTTPRequestHandler, HTTPServer

TELEGRAM_TOKEN = "8149255673:AAH3k_j6Zk8x8bO6N_3YtM1f8bK8m7P_L8w"
TELEGRAM_CHAT_ID = "546949841"

# НЕУЯЗВИМОЕ ЗЕРКАЛО ДЛЯ ОБХОДА БЛОКИРОВОК В РФ
API_URL = "http://worldtimeapi.org"

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")

def run_health_server():
    server = HTTPServer(("0.0.0.0", 10000), HealthCheckHandler)
    server.serve_forever()

def send_telegram_alert(message):
    # Используем открытый зеркальный шлюз вместо заблокированного api.telegram.org!
    url = f"https://tgproxy.site{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        res = requests.post(url, json=payload, timeout=7)
        print(f"Статус шлюза: {res.status_code}")
    except Exception as e:
        print(f"Ошибка шлюза: {e}")

def time_monitoring_loop():
    print("Параллельный мониторинг запущен...")
    time.sleep(5)
    while True:
        try:
            response = requests.get(API_URL, timeout=5)
            if response.status_code == 200:
                current_time = response.json().get("datetime", "Unknown")
                msg = (
                    f"⏰ ЗЕРКАЛЬНЫЙ ШЛЮЗ ПРОБИТ!\n"
                    f"Сервер Render на связи с Айфоном!\n"
                    f"Точное время: {current_time}\n"
                    f"🚀 Бот @Qwerty1244785_bot официально ожил!"
                )
                send_telegram_alert(msg)
        except Exception as e:
            print(f"Ошибка времени: {e}")
        
        # Шлём пуш каждые 15 секунд для проверки связи
        time.sleep(15)

if __name__ == "__main__":
    Thread(target=time_monitoring_loop, daemon=True).start()
    run_health_server()
