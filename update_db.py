import json
import os
import re
from telethon.sync import TelegramClient
from telethon.sessions import StringSession

# === КОНФИГ ===
API_ID = os.environ['TG_API_ID']
API_HASH = os.environ['TG_API_HASH']
SESSION_STRING = os.environ['TG_SESSION']

CHANNEL_USERNAME = 'masonsmansion' 
JSON_FILE = 'posts.json'

# Только посты с этими эмодзи попадут в базу
CATEGORY_MAP = {
    '⚔️': '⚔️ Жизнестойкость',
    '🧠': '🧠 Ошибки мышления',
    '💃': '💃 Женщины',
    '💊': '💊 Здоровье',
    '🎙': '🎙 Медиа',
    '📜': '📜 Фольклор',
    '🔒': '🔒 Гайды/Отчеты'
}

# Настройки фильтра
MIN_LENGTH = 200

def update_json():
    # 1. Загружаем старую базу
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            posts = json.load(f)
    else:
        posts = []

    # Собираем существующие ссылки
    existing_urls = {p['u'] for p in posts}
    
    # 2. Подключаемся к Телеграму
    print("Подключение к Telegram...")
    with TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH) as client:
        # Лимит 50
        for message in client.iter_messages(CHANNEL_USERNAME, limit=50):
            if not message.text:
                continue

            # === ФИЛЬТР 1: ЭМОДЗИ (ФЕЙС-КОНТРОЛЬ) ===
            found_category = None
            for emoji_icon, cat_name in CATEGORY_MAP.items():
                if emoji_icon in message.text:
                    found_category = cat_name
                    break
            
            # Если эмодзи из списка не нашли — пост идет лесом
            if not found_category:
                continue

            # === ФИЛЬТР 2: ЧИСТКА МУСОРА ===
            # Вырезаем "// ПРОДОЛЖЕНИЕ ... //"
            clean_text_body = re.sub(r'//\s*продолжение.*?//', '', message.text, flags=re.IGNORECASE | re.DOTALL).strip()

            # === ФИЛЬТР 3: ДЛИНА ===
            # Если после чистки пост короче 200 символов — скипаем
            if len(clean_text_body) < MIN_LENGTH:
                continue
            
            # =================================

            post_url = f"https://t.me/{CHANNEL_USERNAME}/{message.id}"

            if post_url in existing_urls:
                continue 
            
            # Формируем заголовок
            if '\n' in clean_text_body:
                raw_title = clean_text_body.split('\n')[0].strip()
            else:
                raw_title = clean_text_body 

            # Чистим Markdown в заголовке
            clean_title = re.sub(r'[*_`]', '', raw_title)
            
            # Страховка от кривых заголовков
            if clean_title.startswith('//') or len(clean_title) < 3:
                clean_title = "Без названия"
            
            if len(clean_title) > 100:
                clean_title = clean_title[:97] + "..."

            new_post = {
                "t": clean_title,
                "u": post_url,
                "c": found_category  # Используем найденную категорию
            }
            
            posts.insert(0, new_post)
            print(f"✅ Добавлен пост: {clean_title} -> {found_category}")

    # 3. Сохраняем
    with open(JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    update_json()
