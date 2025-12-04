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

CATEGORY_MAP = {
    '⚔️': '⚔️ Жизнестойкость',
    '🧠': '🧠 Ошибки мышления',
    '💃': '💃 Женщины',
    '💊': '💊 Здоровье',
    '🎙': '🎙 Медиа',
    '📜': '📜 Фольклор',
    '🔒': '🔒 Гайды/Отчеты'
}

DEFAULT_CATEGORY = '⚔️ Жизнестойкость'

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
        # Лимит 50, чтобы не копать слишком глубоко
        for message in client.iter_messages(CHANNEL_USERNAME, limit=50):
            if not message.text:
                continue

            # === БЛОК ЧИСТКИ (ЖЕСТКИЙ) ===
            
            # 1. Вырезаем любое "// ПРОДОЛЖЕНИЕ ... //" независимо от регистра и содержания внутри слешей
            # Флаг re.IGNORECASE позволяет ловить и "ПРОДОЛЖЕНИЕ", и "продолжение"
            # Флаг re.DOTALL позволяет точке . захватывать переносы строк, если мусор размазан
            clean_text_body = re.sub(r'//\s*продолжение.*?//', '', message.text, flags=re.IGNORECASE | re.DOTALL).strip()

            # 2. Если после чистки пост стал коротышом — нахуй его
            if len(clean_text_body) < MIN_LENGTH:
                # print(f"Скипнут мусор/коротыш: {len(clean_text_body)} симв.")
                continue
            
            # =================================

            post_url = f"https://t.me/{CHANNEL_USERNAME}/{message.id}"

            if post_url in existing_urls:
                continue 

            # Категория
            category = DEFAULT_CATEGORY
            for emoji_icon, cat_name in CATEGORY_MAP.items():
                if emoji_icon in message.text:
                    category = cat_name
                    break
            
            # Заголовок
            if '\n' in clean_text_body:
                raw_title = clean_text_body.split('\n')[0].strip()
            else:
                raw_title = clean_text_body 

            # Чистим Markdown
            clean_title = re.sub(r'[*_`]', '', raw_title)
            
            # Доп. проверка: если заголовок все еще выглядит как системный мусор
            if clean_title.startswith('//') or len(clean_title) < 3:
                clean_title = "Без названия"
            
            if len(clean_title) > 100:
                clean_title = clean_title[:97] + "..."

            new_post = {
                "t": clean_title,
                "u": post_url,
                "c": category
            }
            
            posts.insert(0, new_post)
            print(f"✅ Добавлен пост: {clean_title}")

    # 3. Сохраняем
    with open(JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    update_json()
