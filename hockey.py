import requests
from threading import Thread
from http.server import BaseHTTPRequestHandler, HTTPServer

# Официальные рабочие ключи системы Pushover
PUSHOVER_USER_KEY = "u783259837459384759348759348759"
PUSHOVER_TOKEN = "az7msq7v66n76k7vvv3v6v3vvv3vvv"

def async_pushover_send():
    """Отправка системного пуша Apple напрямую через сервера Pushover"""
    url = "https://pushover.net"
    payload = {
        "token": PUSHOVER_TOKEN,
        "user": PUSHOVER_USER_KEY,
        "title": "🏒 live-hockey-radar 🎉",
        "message": "🚀 ПОБЕДА! АСИНХРОННЫЙ ШЛЮЗ APPLE ПРОБИЛ ЭКРАН ТВОЕГО АЙФОНА!"
    }
    try:
        res = requests.post(url, data=payload, timeout=5)
        print(f"Ответ API: {res.status_code}")
    except Exception as e:
        print(f"Ошибка сети: {e}")

class InstantPushHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Запускаем отправку пуша в параллельном независимом потоке
        Thread(target=async_pushover_send, daemon=True).start()

        # Мгновенно отдаем ответ сайту, убирая Port Scan Timeout
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write("СИГНАЛ PUSHOVER ОТПРАВЛЕН В ПОТОК!".encode('utf-8'))

if __name__ == "__main__":
    print("Старт асинхронного Pushover-тестера...")
    server = HTTPServer(("0.0.0.0", 10000), InstantPushHandler)
    server.forever_server = server.serve_forever()
