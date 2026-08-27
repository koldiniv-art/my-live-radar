import time
import requests
from threading import Thread
from http.server import BaseHTTPRequestHandler, HTTPServer

TELEGRAM_TOKEN = "8423957705:AAEMRP72DHn5x0sFtswYMycB0VWUly5ZR7E"
TELEGRAM_CHAT_ID = "546949841"
API_URL = "https://sofascore.com"
HEADERS = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15"}

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def run_health_server():
    HTTPServer(("0.0.0.0", 10000), HealthCheckHandler).serve_forever()

def send_telegram_alert(message):
    url = f"https://telegram.org{TELEGRAM_TOKEN}/sendMessage"
    try: requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}, timeout=5)
    except Exception as e: print(f"Ошибка ТГ: {e}")

def check_test(match_data):
    team_home = match_data.get("homeTeam", {}).get("name", "Home")
    team_away = match_data.get("awayTeam", {}).get("name", "Away")
    score_home = int(match_data.get("homeScore", {}).get("current", 0))
    score_away = int(match_data.get("awayScore", {}).get("current", 0))
    
    # ТЕСТОВЫЙ ТРИГГЕР: Любой идущий матч, где есть хотя бы 1 шайба
    if (score_home + score_away) >= 1:
        msg = (
            f"🏒 *ТЕСТ СВЯЗИ: ХОККЕЙ ЖИВОЙ ЭФИР*\n"
            f"Матч: {team_home} vs {team_away}\n"
            f"Текущий live-счет: {score_home}:{score_away}\n"
            f"✅ Сервер Render успешно парсит хоккей!"
        )
        send_telegram_alert(msg)

def main_loop():
    print("Тестовый ХОККЕЙНЫЙ скрипт запущен...")
    while True:
        try:
            response = requests.get(API_URL, headers=HEADERS, timeout=10)
            if response.status_code == 200:
                for match in response.json().get("events", []): check_test(match)
        except Exception as e: print(f"Ошибка: {e}")
        time.sleep(7)

if __name__ == "__main__":
    Thread(target=run_health_server, daemon=True).start()
    main_loop()
