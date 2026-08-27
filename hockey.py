import time
import requests
from threading import Thread
from http.server import BaseHTTPRequestHandler, HTTPServer

TELEGRAM_TOKEN = "8423957705:AAEMRP72DHn5x0sFtswYMycB0VWUly5ZR7E"
TELEGRAM_CHAT_ID = "546949841"

# 100% открытый шлюз мирового времени. Никаких блокировок и проверок!
API_URL = "http://worldtimeapi.org"

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def run_health_server():
    HTTPServer(("0.0.0.0", 10000), HealthCheckHandler).serve_forever()

def send_telegram_alert(message):
    url = f"https://telegram.org{TELEGRAM_TOKEN}/sendMessage"
    try: requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": message}, timeout=5)
    except Exception as e: print(f"Ошибка ТГ: {e}")

def main_loop():
    print("Ультра-тест связи запущен...")
    while True:
        try:
            response = requests.get(API_URL, timeout=5)
            if response.status_code == 200:
                current_time = response.json().get("datetime", "Unknown")
                msg = (
                    f"⏰ *ТЕСТ СВЯЗИ ПРОЙДЕН УСПЕШНО!*\n"
                    f"Сервер Render полностью живой!\n"
                    f"Точное время на сервере: {current_time}\n"
                    f"🚀 Цепочка связи Рендер -> Айфон монолитна!"
                )
                send_telegram_alert(msg)
        except Exception as e: 
            print(f"Ошибка: {e}")
        
        # Шлём пуш каждые 10 секунд для мгновенной проверки
        time.sleep(10)

if __name__ == "__main__":
    Thread(target=run_health_server, daemon=True).start()
    main_loop()
