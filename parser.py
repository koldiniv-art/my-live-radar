import time
import requests
from threading import Thread
from http.server import BaseHTTPRequestHandler, HTTPServer

# ----------------- НАСТРОЙКИ СИСТЕМЫ -----------------
TELEGRAM_TOKEN = "8423957705:AAEMRP72DHn5x0sFtswYMycB0VWUly5ZR7E"
TELEGRAM_CHAT_ID = "546949841"

# Официальный live-поток серверов Sofascore
API_URL = "https://sofascore.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
}

# --- ВЕБ-СЕРВЕР ДЛЯ ОБХОДА И ЗАПУСКА НА БЕСПЛАТНОМ ТАРИФЕ RENDER (ПОРТ 10001) ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"OK")

def run_health_server():
    server = HTTPServer(("0.0.0.0", 10001), HealthCheckHandler)
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

def check_test_basketball(match_data):
    """Ультра-короткий тест: ловит абсолютно любой живой баскетбольный матч"""
    team_home = match_data.get("homeTeam", {}).get("name", "Home")
    team_away = match_data.get("awayTeam", {}).get("name", "Away")
    
    score_home = int(match_data.get("homeScore", {}).get("current", 0))
    score_away = int(match_data.get("awayScore", {}).get("current", 0))
    total_score = score_home + score_away

    # Если в матче забит хотя бы один мяч — шлем мгновенный пуш для теста связи!
    if total_score >= 2:
        msg = (
            f"🏀 *ТЕСТ СВЯЗИ: БАСКЕТБОЛ ЖИВОЙ ЭФИР*\n"
            f"🏆 Матч: {team_home} vs {team_away}\n"
            f"⏱ Текущий live-счет матча: {score_home}:{score_away} (Сумма: {total_score})\n"
            f"✅ Сервер Render успешно парсит Sofascore на порту 10001!"
        )
        send_telegram_alert(msg)

def main_loop():
    print("Тестовый БАСКЕТБОЛЬНЫЙ скрипт успешно запущен...")
    while True:
        try:
            response = requests.get(API_URL, headers=HEADERS, timeout=10)
            if response.status_code == 200:
                matches_list = response.json().get("events", [])
                for match in matches_list: 
                    check_test_basketball(match)
        except Exception as e: 
            print(f"Ошибка запроса к API: {e}")
        
        # Высокоскоростной шаг опроса — 7 секунд
        time.sleep(7)

if __name__ == "__main__":
    Thread(target=run_health_server, daemon=True).start()
    main_loop()
