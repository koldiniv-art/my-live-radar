import time
import requests
from threading import Thread
from http.server import BaseHTTPRequestHandler, HTTPServer

# --- НАСТРОЙКИ СИСТЕМЫ И ЖИВОЙ ТЕННИСНЫЙ ШЛЮЗ ДЛЯ ТЕСТА СВЯЗИ ---
TELEGRAM_TOKEN = "8423957705:AAEMRP72DHn5x0sFtswYMycB0VWUly5ZR7E"
TELEGRAM_CHAT_ID = "546949841"

# Строка №10: Точный и полный адрес теннисного API-шлюза Sofascore
API_URL = "https://sofascore.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
}

# --- ВЕБ-СЕРВЕР ДЛЯ ОБХОДА И ЗАПУСКА НА БЕСПЛАТНОМ ТАРИФЕ RENDER (ПОРТ 10000) ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"OK")

def run_health_server():
    server = HTTPServer(("0.0.0.0", 10000), HealthCheckHandler)
    server.serve_forever()
# ------------------------------------------------------------------

def send_telegram_alert(message):
    """Мгновенная отправка сигнала в Telegram на твой Айфон"""
    url = f"https://telegram.org{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try: 
        requests.post(url, json=payload, timeout=5)
    except Exception as e: 
        print(f"Ошибка отправки сообщения: {e}")

def check_test_tennis(match_data):
    """Тестовый триггер: шлет пуш по абсолютно любому теннисному матчу в лайве"""
    team_home = match_data.get("homeTeam", {}).get("name", "Home")
    team_away = match_data.get("awayTeam", {}).get("name", "Away")
    
    msg = (
        f"🎾 *УЛЬТРА-ТЕСТ СВЯЗИ: ТЕННИС В ЛАЙВЕ*\n"
        f"🏆 Матч: {team_home} vs {team_away}\n"
        f"✅ Сервер Render работает идеально и видит спорт!"
    )
    send_telegram_alert(msg)

def main_loop():
    print("Ультра-тест тенниса успешно запущен в фоновом режиме...")
    while True:
        try:
            response = requests.get(API_URL, headers=HEADERS, timeout=10)
            if response.status_code == 200:
                events = response.json().get("events", [])
                print(f"Найдено матчей в лайве: {len(events)}")
                for match in events: 
                    check_test_tennis(match)
        except Exception as e: 
            print(f"Ошибка запроса к API: {e}")
        
        # Высокоскоростной интервал опроса — 7 секунд
        time.sleep(7)

if __name__ == "__main__":
    # Запуск параллельного веб-сервера на порту 10000 для удержания бесплатного тарифа Render
    Thread(target=run_health_server, daemon=True).start()
    main_loop()
