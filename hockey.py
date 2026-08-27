import requests
from http.server import BaseHTTPRequestHandler, HTTPServer

# --- НАСТРОЙКИ СИСТЕМЫ С ТВОИМ НОВЫМ ТОЧНЫМ ТОКЕНОМ И ID ---
TELEGRAM_TOKEN = "8149255673:AAH3k_j6Zk8x8bO6N_3YtM1f8bK8m7P_L8w"
TELEGRAM_CHAT_ID = "546949841"

class InstantPushHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # 1. Мгновенно отправляем сигнал в твоего нового бота при любом клике на сайт!
        # Ссылка собрана идеально: api.telegram.org/botTOKEN/sendMessage
        url = f"https://telegram.org{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID, 
            "text": "🚀 ХАРД-ТЕСТ: СВЯЗЬ ПРОБИТА НАПРЯМУЮ С ПОРТА 10000!"
        }
        
        try:
            res = requests.post(url, json=payload, timeout=5)
            if res.status_code == 200:
                status_text = f"Успешно. Статус ТГ: {res.status_code}"
            else:
                status_text = f"Ошибка Telegram API. Код: {res.status_code} | Ответ: {res.text}"
        except Exception as e:
            status_text = f"Ошибка сети ТГ: {e}"

        # 2. Отвечаем браузеру и серверу Render, что всё отлично
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        
        response_message = f"Сайт работает. {status_text}".encode('utf-8')
        self.wfile.write(response_message)

if __name__ == "__main__":
    print("Старт ультра-короткого веб-тестера связи...")
    # Сервер вечно держит порт 10000 для бесплатного тарифа Render
    server = HTTPServer(("0.0.0.0", 10000), InstantPushHandler)
    server.serve_forever()
