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

# Хранилище истории набора очков для точного отслеживания 60-секундных взрывов
MATCH_HISTORY = {}

# --- ВЕБ-СЕРВЕР ДЛЯ ОБХОДА И ЗАПУСКА НА БЕСПЛАТНОМ ТАРИФЕ RENDER ---
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

def check_four_factor_model(match_data):
    """Ядро Версии 3.2: Фильтрация трендов лиги, Box Score скорреров и лимитов времени"""
    
    match_id = str(match_data.get("id", "0"))
    team_home = match_data.get("homeTeam", {}).get("name", "Home")
    team_away = match_data.get("awayTeam", {}).get("name", "Away")
    
    score_home = int(match_data.get("homeScore", {}).get("current", 0))
    score_away = int(match_data.get("awayScore", {}).get("current", 0))
    total_score = score_home + score_away

    status = match_data.get("status", {})
    description = status.get("description", "")
    current_minute = float(status.get("minutes", 0)) if status.get("minutes") else 0.0

    # Автоматически определяем параметры секунд для текущей четверти (ФИБА/ЖНБА — 10 минут)
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
        if match_id in MATCH_HISTORY: del MATCH_HISTORY[match_id]
        return 

    QUARTER_LENGTH = 600
    remaining_seconds = QUARTER_LENGTH - elapsed_seconds_in_quarter

    # Срезы делаем строго на экваторе четверти
    if elapsed_seconds_in_quarter <= 60 or remaining_seconds <= 30:
        return

    # --- ФАКТОР 1: ИСКЛЮЧЕНИЕ КОМАНД С ВЫСОКИМ % РЕАЛИЗАЦИИ ПО ЛИГЕ ---
    # Парсим сезонный показатель FG%. Если данных нет (холодный старт), подставляем безопасную константу лиги 43.5%
    home_season_fg = float(match_data.get("homeTeam", {}).get("statistics", {}).get("fieldGoalPercentage", 43.5))
    away_season_fg = float(match_data.get("awayTeam", {}).get("statistics", {}).get("fieldGoalPercentage", 43.5))
    
    # Жесткий предохранитель: если любая команда системно забивает > 46.5% по лиге — полный пропуск матча!
    if home_season_fg > 46.5 or away_season_fg > 46.5:
        return

    # Запись текущей точки счета в историю матча
    if match_id not in MATCH_HISTORY:
        MATCH_HISTORY[match_id] = []
    MATCH_HISTORY[match_id].append((elapsed_seconds_in_quarter, quarter_score))
    MATCH_HISTORY[match_id] = [t for t in MATCH_HISTORY[match_id] if elapsed_seconds_in_quarter - t <= 60]

    # Расчет триггера «Минутный взрыв» (за последние 60 секунд чистой игры)
    if len(MATCH_HISTORY[match_id]) > 1:
        oldest_point = MATCH_HISTORY[match_id][0]
        points_in_last_minute = quarter_score - oldest_point[1]
    else:
        points_in_last_minute = 0

    # Текущие котировки Betradar и фолы
    bk_live_quarter_total = float(match_data.get("liveTotalLine", 0))
    fouls_home = int(match_data.get("homeFouls", 0))
    fouls_away = int(match_data.get("awayFouls", 0))

    # Данные расширенной статистики бросков с Sofascore
    stats = match_data.get("statistics", {})
    fga_home = int(stats.get("fieldGoalsAttemptedHome", 0))
    fga_away = int(stats.get("fieldGoalsAttemptedAway", 0))
    total_fga = fga_home + fga_away 

    fgm_home = int(stats.get("fieldGoalsMadeHome", 0))
    fgm_away = int(stats.get("fieldGoalsMadeAway", 0))
    total_fgm = fgm_home + fgm_away 

    if total_fga > 0 and elapsed_seconds_in_quarter > 0:
        current_fg_pct = (total_fgm / total_fga * 100)
        points_per_second_in_quarter = quarter_score / elapsed_seconds_in_quarter

        # Линейная экстраполяция темпа на остаток секунд
        max_projected_quarter_total = quarter_score + (points_per_second_in_quarter * remaining_seconds)
        current_pace = (total_fga * 600 / elapsed_seconds_in_quarter) * 4 

        # --- ФАКТОР 2: ИСКЛЮЧЕНИЕ МАТЧЕЙ С 3+ СУПЕР-СКОРРЕРАМИ (BOX SCORE CHECK) ---
        # Сканируем live-список игроков на предмет запредельного индивидуального куража
        players_sharing = match_data.get("playersPerformance", [])
        super_scorers_count = 0
        for player in players_sharing:
            p_points = int(player.get("points", 0))
            p_fga = int(player.get("fieldGoalsAttempted", 0))
            p_fgm = int(player.get("fieldGoalsMade", 0))
            p_fg_pct = (p_fgm / p_fga * 100) if p_fga > 0 else 0
            # Если игрок уже набрал >= 8 очков с реализацией >= 60% — это супер-скорреер
            if p_points >= 8 and p_fg_pct >= 60.0:
                super_scorers_count += 1
        
        # Если таких "горячих" лидеров на паркете 3 или больше — ротация лавки не спасет ТМ. Сброс!
        if super_scorers_count >= 3:
            return

        # 🛡 КРИТИЧЕСКИЕ ПРЕДОХРАНИТЕЛИ БЕЗОПАСНОСТИ БАНКА
        if fouls_home > 2 or fouls_away > 2: return  # Ранние фолы сожрут ТМ штрафными
        if current_pace > 95.0: return  # Исключаем тотальный хаос "бей-беги" без тренера

        # 🎯 ДИНАМИЧЕСКИЙ ТРИГГЕР ВЕРСИИ 3.2:
        if points_in_last_minute >= 8 and current_fg_pct >= 58.0:
            if bk_live_quarter_total > max_projected_quarter_total:
                
                value_delta = bk_live_quarter_total - max_projected_quarter_total

                if value_delta >= 1.5:
                    msg = (
                        f"🚨 *БАСКЕТБОЛ: ИНТЕЛЛЕКТУАЛЬНЫЙ ТРИГГЕР (ТМ)*\n"
                        f"🏀 Матч: {team_home} vs {team_away}\n"
                        f"⏱ Минута матча: {current_minute:.1f} | Счет четверти: {quarter_score}\n"
                        f"🔥 Шок-вспышка: +{points_in_last_minute} очк. за 60 сек!\n"
                        f"📊 Pace: {current_pace:.1f} | Реализация: {current_fg_pct:.1f}%\n"
                        f"📈 Предел секунд матча: *{max_projected_quarter_total:.1f}*\n"
                        f"📉 Перегретая линия БК: *{bk_live_quarter_total:.1f}*\n"
                        f"🎁 Чистый валуй: +{value_delta:.1f} очка!\n\n"
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
        
        # Высокоскоростной шаг опроса — 7 секунд
        time.sleep(7)

if __name__ == "__main__":
    Thread(target=run_health_server, daemon=True).start()
    main_loop()
