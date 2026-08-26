import time
import requests
from threading import Thread
from http.server import BaseHTTPRequestHandler, HTTPServer

# ----------------- НАСТРОЙКИ СИСТЕМЫ -----------------
TELEGRAM_TOKEN = "8423957705:AAEMRP72DHn5x0sFtswYMycB0VWUly5ZR7E"
TELEGRAM_CHAT_ID = "546949841"

# Официальный live-поток хоккейных серверов Sofascore
API_URL = "https://sofascore.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
}

# Хранилище истории шайб для отслеживания 60-секундных взрывов в хоккее
HOCKEY_HISTORY = {}

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

def check_hockey_model(match_data):
    """Хоккейное ядро: 20-минутный лимит, контроль удалений и % реализации бросков"""
    
    match_id = str(match_data.get("id", "0"))
    team_home = match_data.get("homeTeam", {}).get("name", "Home")
    team_away = match_data.get("awayTeam", {}).get("name", "Away")
    
    # Извлекаем текущий статус и минуту периода
    status = match_data.get("status", {})
    description = status.get("description", "")
    current_minute = float(status.get("minutes", 0)) if status.get("minutes") else 0.0

    # Определяем, идет ли чистая игра внутри 1, 2 или 3 периода (каждый по 20 минут чистой игры)
    if "1st period" in description.lower():
        elapsed_seconds_in_period = current_minute * 60
        score_home = int(match_data.get("homeScore", {}).get("period1", 0))
        score_away = int(match_data.get("awayScore", {}).get("period1", 0))
    elif "2nd period" in description.lower():
        elapsed_seconds_in_period = (current_minute - 20) * 60
        score_home = int(match_data.get("homeScore", {}).get("period2", 0))
        score_away = int(match_data.get("awayScore", {}).get("period2", 0))
    elif "3rd period" in description.lower():
        elapsed_seconds_in_quarter = (current_minute - 40) * 60
        score_home = int(match_data.get("homeScore", {}).get("period3", 0))
        score_away = int(match_data.get("awayScore", {}).get("period3", 0))
    else:
        if match_id in HOCKEY_HISTORY: del HOCKEY_HISTORY[match_id]
        return

    period_score = score_home + score_away
    PERIOD_LENGTH = 1200 # 20 минут чистой игры в хоккее
    remaining_seconds = PERIOD_LENGTH - elapsed_seconds_in_period

    # Срезы делаем строго в диапазоне от 4-й до 12-й минуты периода (разгар игры)
    if elapsed_seconds_in_period < 240 or elapsed_seconds_in_period > 720:
        return

    # --- КРИТИЧЕСКИЙ ПРЕДОХРАНИТЕЛЬ №5: УДАЛЕНИЯ (POWER PLAY) ---
    # Если на льду прямо сейчас идет большинство — немедленный сброс и выход!
    if match_data.get("status", {}).get("isPowerPlay", False) == True:
        return

    # Запись текущей точки счета в историю хоккейного матча
    if match_id not in HOCKEY_HISTORY:
        HOCKEY_HISTORY[match_id] = []
    HOCKEY_HISTORY[match_id].append((elapsed_seconds_in_period, period_score))
    HOCKEY_HISTORY[match_id] = [t for t in HOCKEY_HISTORY[match_id] if elapsed_seconds_in_period - t <= 60]

    # Расчет минутного взрыва шайб (за последние 60 секунд чистой игры)
    if len(HOCKEY_HISTORY[match_id]) > 1:
        goals_in_last_minute = period_score - HOCKEY_HISTORY[match_id][0][1]
    else:
        goals_in_last_minute = 0

    # Извлекаем броски в створ (Shots on Goal) с Sofascore
    stats = match_data.get("statistics", {})
    shots_home = int(stats.get("shotsOnGoalHome", 0))
    shots_away = int(stats.get("shotsOnGoalAway", 0))
    total_shots = shots_home + shots_away

    # Линия тотала текущего периода от Betradar
    bk_live_period_total = float(match_data.get("livePeriodTotalLine", 0))

    if total_shots > 0 and elapsed_seconds_in_period > 0:
        # Текущий процент реализации бросков (SH%) и базовая экстраполяция
        current_sh_pct = (period_score / total_shots * 100)
        goals_per_second = period_score / elapsed_seconds_in_period
        
        # Вычисляем истинный математический предел периода на остаток секунд
        max_projected_period_total = period_score + (goals_per_second * remaining_seconds)

        # --- КРИТИЧЕСКИЙ ПРЕДОХРАНИТЕЛЬ №1: ПРОВЕРКА ВРАТАРЯ БЭКАПА ---
        # Если у стартового кипера плохая статистика — пропускаем (надежность ТМ падает)
        home_goalkeeper_main = match_data.get("homeGoalkeeper", {}).get("isStarter", True)
        away_goalkeeper_main = match_data.get("awayGoalkeeper", {}).get("isStarter", True)
        if not home_goalkeeper_main or not away_goalkeeper_main:
            return

        # 🎯 ХОККЕЙНЫЙ ТРИГГЕР: Минутная вспышка в 2+ шайбы, аномальный SH% >= 25%
        # И букмекер под паникой толпы задирает тотал (например, до 5.5 при пределе 4.5)
        if goals_in_last_minute >= 2 and current_sh_pct >= 25.0:
            if bk_live_period_total > max_projected_period_total:
                
                value_delta = bk_live_period_total - max_projected_period_total

                # Сигнал генерируется, если чистый валуй в периоде составляет от 1.0 шайбы и выше
                if value_delta >= 1.0:
                    msg = (
                        f"🏒 *ХОККЕЙ: ИНЕРЦИОННЫЙ КАПКАН (ТМ)*\n"
                        f"🏆 Матч: {team_home} vs {team_away}\n"
                        f"⏱ Минута периода: {current_minute:.1f} | Шайб в периоде: {period_score}\n"
                        f"🔥 Шок-вспышка: +{goals_in_last_minute} гола за 60 сек!\n"
                        f"📊 Броски в створ: {total_shots} | Реализация: {current_sh_pct:.1f}%\n"
                        f"📈 Матем. предел периода: *{max_projected_period_total:.1f}*\n"
                        f"📉 Перегретая линия БК: *{bk_live_quarter_total:.1f}*\n"
                        f"🎁 Чистый валуй: +{value_delta:.1f} шайбы!\n\n"
                        f"🔥 *ДЕЙСТВИЕ:* Ординар на ТМ {bk_live_period_total} в текущем периоде! 🔒"
                    )
                    send_telegram_alert(msg)

def main_loop():
    print("Хоккейный софт успешно запущен на Render. Мониторинг КХЛ/НХЛ активен...")
    while True:
        try:
            response = requests.get(API_URL, headers=HEADERS, timeout=10)
            if response.status_code == 200:
                matches_list = response.json().get("events", [])
                for match in matches_list: 
                    check_hockey_model(match)
        except Exception as e: 
            print(f"Ошибка запроса к хоккейному API: {e}")
        
        # Высокоскоростной шаг опроса — 7 секунд
        time.sleep(7)

if __name__ == "__main__":
    Thread(target=run_health_server, daemon=True).start()
    main_loop()
