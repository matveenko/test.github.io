import json
import os
import re
from telethon.sync import TelegramClient
from telethon.sessions import StringSession

# === КОНФИГ ===
# Берем секреты из переменных окружения
API_ID = os.environ['TG_API_ID']
API_HASH = os.environ['TG_API_HASH']
SESSION_STRING = os.environ['TG_SESSION']

# Юзернейм открытого канала
CHANNEL_USERNAME = 'masonsmansion' 
JSON_FILE = 'posts.json'

# Карта эмодзи -> Твои рубрики из data.js
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
TRASH_PHRASE = "// продолжение поста //"

def update_json():
    # 1. Загружаем старую базу
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            posts = json.load(f)
    else:
        posts = []

    # Собираем существующие ссылки, чтобы не дублировать
    existing_urls = {p['u'] for p in posts}
    
    # 2. Подключаемся к Телеграму
    print("Подключение к Telegram...")
    with TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH) as client:
        # Берем последние 50 постов
        for message in client.iter_messages(CHANNEL_USERNAME, limit=50):
            if not message.text:
                continue

            # === БЛОК ЧИСТКИ И ФИЛЬТРАЦИИ ===
            
            # Сначала вырезаем мусорную фразу и чистим пробелы
            clean_text_body = message.text.replace(TRASH_PHRASE, "").strip()

            # Если после чистки пост короче 200 символов - скипаем его нахуй
            if len(clean_text_body) < MIN_LENGTH:
                # print(f"Скипнут короткий пост (id {message.id}): {len(clean_text_body)} симв.")
                continue
            
            # =================================

            # Ссылка на пост в открытом канале
            post_url = f"https://t.me/{CHANNEL_USERNAME}/{message.id}"

            if post_url in existing_urls:
                continue # Уже есть

            # Определяем категорию по эмодзи (ищем в оригинальном тексте, так надежнее)
            category = DEFAULT_CATEGORY
            for emoji_icon, cat_name in CATEGORY_MAP.items():
                if emoji_icon in message.text:
                    category = cat_name
                    break
            
            # Заголовок берем из ОЧИЩЕННОГО текста
            if '\n' in clean_text_body:
                raw_title = clean_text_body.split('\n')[0].strip()
            else:
                raw_title = clean_text_body 

            # Чистим Markdown в заголовке
            clean_title = re.sub(r'[*_`]', '', raw_title)
            
            if not clean_title:
                clean_title = "Без названия"
            
            if len(clean_title) > 100:
                clean_title = clean_title[:97] + "..."

            new_post = {
                "t": clean_title,
                "u": post_url,
                "c": category
            }
            
            # Добавляем в начало
            posts.insert(0, new_post)
            print(f"Добавлен пост: {clean_title} -> {category}")

    # 3. Сохраняем
    with open(JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    update_json()
