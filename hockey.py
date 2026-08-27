import requests
from threading import Thread
from http.server import BaseHTTPRequestHandler, HTTPServer

TELEGRAM_TOKEN = "8149255673:AAH3k_j6Zk8x8bO6N_3YtM1f8bK8m7P_L8w"
TELEGRAM_CHAT_ID = "546949841"

def async_telegram_send():
    """Отправка пуша в Telegram в изолированном фоновом потоке"""
    url = f"https://telegram.org{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID, 
        "text": "🚀 ХАРД-ТЕСТ: ПАРАЛЛЕЛЬНЫЙ ПОТОК ПРОБИЛ ЭКРАН ТЕЛЕФОНА!"
    }
    try:
        requests.post(url, json=payload, timeout=5)
        print("Сигнал успешно отправлен в Telegram.")
    except Exception as e:
        print(f"Ошибка в потоке ТГ: {e}")

class InstantPushHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # 1. Мгновенно запускаем отправку в Telegram в ОТДЕЛЬНОМ потоке
        # Сервер не будет ждать ответа от Дурова и не зависнет!
        Thread(target=async_telegram_send, daemon=True).start()

        # 2. Мгновенно отдаем ответ сайту
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write("ПОТОК ОТПРАВКИ ЗАПУЩЕН УСПЕШНО!".encode('utf-8'))

if __name__ == "__main__":
    print("Старт асинхронного тестера связи...")
    server = HTTPServer(("0.0.0.0", 10000), InstantPushHandler)
    server.serve_forever()
