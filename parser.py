import time
import requests
from threading import Thread
from http.server import BaseHTTPRequestHandler, HTTPServer

# ----------------- НАСТРОЙКИ СИСТЕМЫ -----------------
TELEGRAM_TOKEN = "8423957705:AAEMRP72DHn5x0sFtswYMycB0VWUly5ZR7E"
TELEGRAM_CHAT_ID = "546949841"

API_URL = "https://sofascore.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
}

MATCH_HISTORY = {}

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
    url = f"https://telegram.org{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try: requests.post(url, json=payload, timeout=5)
    except Exception as e: print(f"Ошибка ТГ: {e}")

def check_four_factor_model(match_data):
    match_id = str(match_data.get("id", "0"))
    team_home = match_data.get("homeTeam", {}).get("name", "Home")
    team_away = match_data.get("awayTeam", {}).get("name", "Away")
    
    score_home = int(match_data.get("homeScore", {}).get("current", 0))
    score_away = int(match_data.get("awayScore", {}).get("current", 0))
    total_score = score_home + score_away
    score_delta = abs(score_home - score_away)

    status = match_data.get("status", {})
    description = status.get("description", "")
    current_minute = float(status.get("minutes", 0)) if status.get("minutes") else 0.0

    is_fourth_quarter = "4th quarter" in description.lower()
    
    if "1st quarter" in description.lower():
        elapsed_seconds_in_quarter = current_minute * 60
        quarter_score = total_score
    elif "2nd quarter" in description.lower():
        elapsed_seconds_in_quarter = (current_minute - 10) * 60
        quarter_score = total_score - int(match_data.get("homeScore", {}).get("period1", 0)) - int(match_data.get("awayScore", {}).get("period1", 0))
    elif "3rd quarter" in description.lower():
        elapsed_seconds_in_quarter = (current_minute - 20) * 60
        quarter_score = total_score - int(match_data.get("homeScore", {}).get("period1", 0)) - int(match_data.get("awayScore", {}).get("period1", 0)) - int(match_data.get("homeScore", {}).get("period2", 0)) - int(match_data.get("awayScore", {}).get("period2", 0))
    elif is_fourth_quarter:
        elapsed_seconds_in_quarter = (current_minute - 30) * 60
        quarter_score = total_score - int(match_data.get("homeScore", {}).get("period1", 0)) - int(match_data.get("awayScore", {}).get("period1", 0)) - int(match_data.get("homeScore", {}).get("period2", 0)) - int(match_data.get("awayScore", {}).get("period2", 0)) - int(match_data.get("homeScore", {}).get("period3", 0)) - int(match_data.get("awayScore", {}).get("period3", 0))
    else:
        if match_id in MATCH_HISTORY: del MATCH_HISTORY[match_id]
        return 

    QUARTER_LENGTH = 600
    remaining_seconds = QUARTER_LENGTH - elapsed_seconds_in_quarter

    if elapsed_seconds_in_quarter <= 60 or remaining_seconds <= 30:
        return

    if match_id not in MATCH_HISTORY: MATCH_HISTORY[match_id] = []
    MATCH_HISTORY[match_id].append((elapsed_seconds_in_quarter, quarter_score))
    MATCH_HISTORY[match_id] = [t for t in MATCH_HISTORY[match_id] if elapsed_seconds_in_quarter - t <= 60]

    if len(MATCH_HISTORY[match_id]) > 1:
        points_in_last_minute = quarter_score - MATCH_HISTORY[match_id]
    else: points_in_last_minute = 0

    bk_live_quarter_total = float(match_data.get("liveTotalLine", 0))
    fouls_home = int(match_data.get("homeFouls", 0))
    fouls_away = int(match_data.get("awayFouls", 0))

    stats = match_data.get("statistics", {})
    total_fga = int(stats.get("fieldGoalsAttemptedHome", 0)) + int(stats.get("fieldGoalsAttemptedAway", 0))
    total_fgm = int(stats.get("fieldGoalsMadeHome", 0)) + int(stats.get("fieldGoalsMadeAway", 0))

    if total_fga > 0 and elapsed_seconds_in_quarter > 0:
        current_fg_pct = (total_fgm / total_fga * 100)
        points_per_second_in_quarter = quarter_score / elapsed_seconds_in_quarter
        max_projected_quarter_total = quarter_score + (points_per_second_in_quarter * remaining_seconds)
        current_pace = (total_fga * 600 / elapsed_seconds_in_quarter) * 4 

        # --- БЛОК №2: СНАЙПЕРСКИЙ ТРИГГЕР «МУСОРНОЕ ВРЕМЯ ПОСЛЕ ТАЙМ-АУТА» (35 - 38 МИНУТА) ---
        if is_fourth_quarter and 300 <= elapsed_seconds_in_quarter <= 480: # Строго 35-38 минуты матча
            # 1. Фильтр разгрома (Δ >= 14 очков) и чистого времени по фолам (<= 2)
            if score_delta >= 14 and fouls_home <= 2 and fouls_away <= 2:
                
                # 2. Вычисляем эффективность основы (за первые 3 четверти)
                total_fga_past = int(stats.get("fieldGoalsAttemptedHomePast", 1)) + int(stats.get("fieldGoalsAttemptedAwayPast", 1))
                total_fgm_past = int(stats.get("fieldGoalsMadeHomePast", 0)) + int(stats.get("fieldGoalsMadeAwayPast", 0))
                past_fg_pct = (total_fgm_past / total_fga_past * 100) if total_fga_past > 0 else 45.0
                
                # 3. Фильтр «Мёртвой лавки»: текущая реализация 4-й четверти строго ниже нормы основы минимум на 8%
                # И общий темп лавки упал (длинные позиционные атаки)
                if current_fg_pct <= (past_fg_pct - 8.0) and current_pace < 75.0:
                    
                    # 4. Ловим БК на инерции: тотал перегрет выше секундного предела времени
                    if bk_live_quarter_total > max_projected_quarter_total + 1.5:
                        msg = (
                            f"🗑 *ЖНБА: МУСОРНОЕ ВРЕМЯ (ТМ)*\n"
                            f"🏀 Матч: {team_home} vs {team_away}\n"
                            f"⏱ Точка: {current_minute:.1f} мин | Разгром: Δ {score_delta} очков\n"
                            f"🔥 ТАЙМ-АУТ ЗАКРЫТ: Звезды на банке!\n"
                            f"💤 Мёртвая лавка мажет: {current_fg_pct:.1f}% (Основа била {past_fg_pct:.1f}%)\n"
                            f"📉 Перегретая линия БК: *{bk_live_quarter_total:.1f}* (Предел: {max_projected_quarter_total:.1f})\n\n"
                            f"🔥 *ДЕЙСТВИЕ:* Срочный ординар на ТМ в 4-й четверти! 🔒"
                        )
                        send_telegram_alert(msg)
                        return

        # --- БЛОК №1: СТАНДАРТНЫЙ МИНУТНЫЙ ВЗРЫВ (ОСНОВНОЙ ТРИГГЕР С СУПЕР-ФИЛЬТРАМИ) ---
        home_season_fg = float(match_data.get("homeTeam", {}).get("statistics", {}).get("fieldGoalPercentage", 43.5))
        away_season_fg = float(match_data.get("awayTeam", {}).get("statistics", {}).get("fieldGoalPercentage", 43.5))
        if home_season_fg > 46.5 or away_season_fg > 46.5: return

        super_scorers_count = 0
        for player in match_data.get("playersPerformance", []):
            p_fga = int(player.get("fieldGoalsAttempted", 0))
            if int(player.get("points", 0)) >= 8 and ((int(player.get("fieldGoalsMade", 0)) / p_fga * 100) if p_fga > 0 else 0) >= 60.0: 
                super_scorers_count += 1
        if super_scorers_count >= 3: return

        if fouls_home > 2 or fouls_away > 2: return  
        if current_pace > 95.0: return  

        if points_in_last_minute >= 8 and current_fg_pct >= 58.0:
            if bk_live_quarter_total > max_projected_quarter_total:
                value_delta = bk_live_quarter_total - max_projected_quarter_total
                if value_delta >= 1.5:
                    msg = (
                        f"🚨 *БАСКЕТБОЛ: МИНУТНЫЙ ВЗРЫВ (ТМ)*\n"
                        f"🏀 Матч: {team_home} vs {team_away}\n"
                        f"⏱ Минута матча: {current_minute:.1f} | Счет четверти: {quarter_score}\n"
                        f"🔥 Вспышка: +{points_in_last_minute} очк. за 60 сек!\n"
                        f"📊 Реализация: {current_fg_pct:.1f}%\n"
                        f"📈 Предел секунд: *{max_projected_quarter_total:.1f}*\n"
                        f"📉 Линия БК: *{bk_live_quarter_total:.1f}*\n"
                        f"🎁 Валуй: +{value_delta:.1f} очка!\n\n"
                        f"🔥 *ДЕЙСТВИЕ:* Ординар на ТМ {bk_live_quarter_total} в четверти! 🔒"
                    )
                    send_telegram_alert(msg)

def main_loop():
    print("Софт успешно запущен на Render. Мониторинг активен...")
    while True:
        try:
            response = requests.get(API_URL, headers=HEADERS, timeout=10)
            if response.status_code == 200:
                matches_list = response.json().get("events", [])
                for match in matches_list: check_four_factor_model(match)
        except Exception as e: print(f"Ошибка запроса: {e}")
        time.sleep(7)

if __name__ == "__main__":
    Thread(target=run_health_server, daemon=True).start()
    main_loop()
