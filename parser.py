import time
import requests
from threading import Thread
from http.server import BaseHTTPRequestHandler, HTTPServer

# ----------------- НАСТРОЙКИ СИСТЕМЫ -----------------
TELEGRAM_TOKEN = "8423957705:AAEMRP72DHn5x0sFtswYMycB0VWUly5ZR7E"
TELEGRAM_CHAT_ID = "546949841"

# Официальный live-поток серверов Sofascore
API_URL = "https://sofascore.com"

# Маскировка под реальный браузер Safari на Айфоне для обхода блокировок 403
HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
}

# --- ВЕБ-СЕРВЕР ДЛЯ ОБХОДА И ЗАПУСКА НА БЕСПЛАТНОМ ТАРИФЕ RENDER ---
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

def check_four_factor_model(match_data):
    """Четырехфакторное ядро: Pace, Реализация, Настрел, Тотал БК"""
    
    # Парсим названия команд из структуры Sofascore
    team_home = match_data.get("homeTeam", {}).get("name", "Home")
    team_away = match_data.get("awayTeam", {}).get("name", "Away")
    
    # Парсим live-счет матча
    score_home = int(match_data.get("homeScore", {}).get("current", 0))
    score_away = int(match_data.get("awayScore", {}).get("current", 0))
    total_score = score_home + score_away

    # Извлекаем текущий статус и минуту игры
    status = match_data.get("status", {})
    description = status.get("description", "")
    current_minute = float(status.get("minutes", 0)) if status.get("minutes") else 0.0

    # Автоматически определяем параметры оставшегося времени для текущей четверти (ФИБА/ЖНБА)
    if "1st quarter" in description.lower():
        elapsed_seconds_in_quarter = current_minute * 60
        quarter_score = total_score
    elif "2nd quarter" in description.lower():
        elapsed_seconds_in_quarter = (current_minute - 10) * 60
        quarter_score = total_score - int(match_data.get("homeScore", {}).get("period1", 0)) - int(match_data.get("awayScore", {}).get("period1", 0))
    elif "3rd quarter" in description.lower():
        elapsed_seconds_in_quarter = (current_minute - 20) * 60
        quarter_score = total_score - int(match_data.get("homeScore", {}).get("period1", 0)) - int(match_data.get("awayScore", {}).get("period1", 0)) - int(match_data.get("homeScore", {}).get("period2", 0)) - int(match_data.get("awayScore", {}).get("period2", 0))
    elif "4th quarter" in description.lower():
        elapsed_seconds_in_quarter = (current_minute - 30) * 60
        quarter_score = total_score - int(match_data.get("homeScore", {}).get("period1", 0)) - int(match_data.get("awayScore", {}).get("period1", 0)) - int(match_data.get("homeScore", {}).get("period2", 0)) - int(match_data.get("awayScore", {}).get("period2", 0)) - int(match_data.get("homeScore", {}).get("period3", 0)) - int(match_data.get("awayScore", {}).get("period3", 0))
    else:
        return # Игра еще не началась или перерыв

    # Длина четверти ФИБА/ЖНБА — 10 минут (600 секунд)
    QUARTER_LENGTH = 600
    remaining_seconds = QUARTER_LENGTH - elapsed_seconds_in_quarter

    # Парсим текущую live-планку Тотала Четверти от Betradar и фолы
    bk_live_quarter_total = float(match_data.get("liveTotalLine", 0))
    fouls_home = int(match_data.get("homeFouls", 0))
    fouls_away = int(match_data.get("awayFouls", 0))

    # Извлекаем бросковые данные Advanced Stats с Sofascore
    stats = match_data.get("statistics", {})
    fga_home = int(stats.get("fieldGoalsAttemptedHome", 0))
    fga_away = int(stats.get("fieldGoalsAttemptedAway", 0))
    total_fga = fga_home + fga_away 

    fgm_home = int(stats.get("fieldGoalsMadeHome", 0))
    fgm_away = int(stats.get("fieldGoalsMadeAway", 0))
    total_fgm = fgm_home + fgm_away 

    # Делаем срез строго на экваторе четверти (от 4.0 до 6.5 минут чистой игры)
    if 4.0 <= elapsed_seconds_in_quarter / 60 <= 6.5 and elapsed_seconds_in_quarter > 0:
        
        current_fg_pct = (total_fgm / total_fga * 100) if total_fga > 0 else 0
        points_per_second_in_quarter = quarter_score / elapsed_seconds_in_quarter

        # Формула экстраполяции темпа: математический предел на остаток секунд четверти
        max_projected_quarter_total = quarter_score + (points_per_second_in_quarter * remaining_seconds)
        current_pace = (total_fga * 600 / elapsed_seconds_in_quarter) * 4 

        # 🛡 КРИТИЧЕСКИЕ ПРЕДОХРАНИТЕЛИ БЕЗОПАСНОСТИ БАНКА
        if fouls_home > 2 or fouls_away > 2: return  # Ранние фолы сожрут ТМ штрафными
        if current_pace > 95.0: return  # Сверхзвуковой хаос ломает формулу

        # 🎯 ТРИГГЕР: Настрел больше 30 и Линия БК выше математически возможного максимума времени
        if quarter_score >= 30 and bk_live_quarter_total > max_projected_quarter_total:
            
            value_delta = bk_live_quarter_total - max_projected_quarter_total

            msg = (
                f"🚨 *ТРИГГЕР: ЛОВУШКА ИНЕРЦИИ БК (ТМ)*\n"
                f"🏀 Матч: {team_home} vs {team_away}\n"
                f"⏱ Минута матча: {current_minute:.1f} | Счет четверти: {quarter_score}\n"
                f"📊 Pace: {current_pace:.1f} | Реализация: {current_fg_pct:.1f}%\n"
                f"📈 Предел при сохр. темпа: *{max_projected_quarter_total:.1f}*\n"
                f"📉 Линия Тотала БК в лайве: *{bk_live_quarter_total:.1f}*\n"
                f"🎁 Чистый перевес: +{value_delta:.1f} очка!\n\n"
                f"🔥 *ДЕЙСТВИЕ:* Ординар на ТМ {bk_live_quarter_total} в текущей четверти! 🔒"
            )
            send_telegram_alert(msg)

def main_loop():
    print("Софт успешно запущен на Render. Мониторинг активен...")
    while True:
        try:
            response = requests.get(API_URL, headers=HEADERS, timeout=10)
            if response.status_code == 200:
                matches_list = response.json().get("events", [])
                for match in matches_list: 
                    check_four_factor_model(match)
        except Exception as e: 
            print(f"Ошибка запроса к API: {e}")
        
        # Высокоскоростной интервал опроса: 7 секунд
        time.sleep(7)

if __name__ == "__main__":
    # Запуск параллельного веб-сервера на порту 10000 для удержания бесплатного тарифа Render
    Thread(target=run_health_server, daemon=True).start()
    main_loop()
