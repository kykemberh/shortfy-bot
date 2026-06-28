import telebot
import requests
import psycopg2
import schedule
import threading
import time
from datetime import datetime, timedelta
from telebot import types

BOT_TOKEN = "8973743279:AAGk0bLOogSENf2weOGwwASSICG6EOYM4PE"
GROQ_KEY = "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"
DATABASE_URL = "postgresql://postgres:zMUijLKmLdpsNuelFlglphPchUDCkris@postgres.railway.internal:5432/railway"

bot = telebot.TeleBot(BOT_TOKEN)

# ===== БАЗА ДАНИХ =====
def get_db():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            uid BIGINT PRIMARY KEY,
            username TEXT,
            niche TEXT,
            generations INT DEFAULT 0,
            joined TIMESTAMP DEFAULT NOW()
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS daily_trend (
            id SERIAL PRIMARY KEY,
            trend TEXT,
            date DATE DEFAULT CURRENT_DATE
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

def register_user(uid, username):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO users (uid, username) VALUES (%s, %s) ON CONFLICT DO NOTHING", (uid, username))
    conn.commit()
    cur.close()
    conn.close()

def increment_generations(uid):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE users SET generations = generations + 1 WHERE uid = %s", (uid,))
    conn.commit()
    cur.close()
    conn.close()

def get_leaderboard():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT username, generations FROM users ORDER BY generations DESC LIMIT 10")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def save_niche(uid, niche):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE users SET niche = %s WHERE uid = %s", (niche, uid))
    conn.commit()
    cur.close()
    conn.close()

def get_niche(uid):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT niche FROM users WHERE uid = %s", (uid,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row and row[0] else None

def get_all_users():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT uid FROM users")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [r[0] for r in rows]

def save_trend(trend):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM daily_trend")
    cur.execute("INSERT INTO daily_trend (trend) VALUES (%s)", (trend,))
    conn.commit()
    cur.close()
    conn.close()

def get_trend():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT trend FROM daily_trend ORDER BY id DESC LIMIT 1")
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else None

# ===== GROQ =====
user_history = {}

def ask_groq(messages):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": messages
    }
    response = requests.post(url, headers=headers, json=payload)
    return response.json()["choices"][0]["message"]["content"]

SYSTEM_PROMPT = """You are an expert viral content creator and online money-making coach.

Your skills:
- Writing viral scripts for YouTube Shorts, TikTok, Instagram Reels (American audience)
- Analyzing YouTube channels and giving specific growth advice
- Teaching people how to make money online: YouTube, TikTok, Freelance, Dropshipping
- Creating A/B hook tests, content plans, trending ideas

When generating scripts always include:
- [HOOK — 0-3 sec]
- [STORY — 3-33 sec]  
- [CLOSING — 33-35 sec]
- 3 title options
- 10 hashtags

Always respond in the same language the user writes in.
Be specific and actionable, not generic."""

def get_history(uid):
    if uid not in user_history:
        user_history[uid] = [{"role": "system", "content": SYSTEM_PROMPT}]
    return user_history[uid]

def add_to_history(uid, role, content):
    history = get_history(uid)
    history.append({"role": role, "content": content})
    if len(history) > 20:
        user_history[uid] = [history[0]] + history[-10:]

# ===== МЕНЮ =====
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🎬 Згенерувати сценарій")
    markup.add("🔥 Трендова ідея дня", "📅 Контент план на 7 днів")
    markup.add("📊 Аналіз каналу", "🎯 A/B тест хуків")
    markup.add("💰 Як заробити онлайн", "🏆 Лідерборд")
    markup.add("⚙️ Моя ніша", "💬 Чат з AI")
    return markup

# ===== ЩОДЕННІ ПОВІДОМЛЕННЯ =====
def send_daily_motivation():
    users = get_all_users()
    prompt = "Give a short powerful morning motivation (3 sentences) for content creators trying to grow online. Then give 1 specific actionable tip for today. Be inspiring and practical."
    try:
        msg = ask_groq([{"role": "user", "content": prompt}])
        for uid in users:
            try:
                bot.send_message(uid, f"🌅 Доброго ранку!\n\n{msg}\n\n🚀 Вперед до успіху!")
            except:
                pass
    except:
        pass

def generate_daily_trend():
    prompt = "What is ONE viral trending topic right now for YouTube Shorts that would get millions of views targeting American audience? Give topic name and 2 sentence explanation why it's trending. Be specific."
    try:
        trend = ask_groq([{"role": "user", "content": prompt}])
        save_trend(trend)
    except:
        pass

def schedule_jobs():
    schedule.every().day.at("10:00").do(send_daily_motivation)
    schedule.every().day.at("08:00").do(generate_daily_trend)
    while True:
        schedule.run_pending()
        time.sleep(60)

# ===== ХЕНДЛЕРИ =====
@bot.message_handler(commands=['start'])
def start(message):
    uid = message.chat.id
    username = message.from_user.username or message.from_user.first_name
    register_user(uid, username)
    get_history(uid)

    niche = get_niche(uid)
    niche_text = f"Твоя ніша: *{niche}*" if niche else "Ніша не вказана — натисни ⚙️ Моя ніша"

    bot.send_message(uid,
        f"👋 Привіт, {message.from_user.first_name}!\n\n"
        "Я твій AI помічник для вірусного контенту і заробітку онлайн!\n\n"
        f"📌 {niche_text}\n\n"
        "Що робимо сьогодні? 👇",
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda m: True)
def handle(message):
    uid = message.chat.id
    text = message.text
    username = message.from_user.username or message.from_user.first_name
    register_user(uid, username)

    # ЛІДЕРБОРД
    if text == "🏆 Лідерборд":
        rows = get_leaderboard()
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        msg = "🏆 *Топ користувачів цього тижня:*\n\n"
        for i, (uname, gens) in enumerate(rows):
            msg += f"{medals[i]} @{uname} — {gens} генерацій\n"
        bot.send_message(uid, msg, parse_mode="Markdown", reply_markup=main_menu())
        return

    # ТРЕНДОВА ІДЕЯ
    if text == "🔥 Трендова ідея дня":
        trend = get_trend()
        if not trend:
            generate_daily_trend()
            trend = get_trend()
        bot.send_message(uid, f"🔥 *Трендова ідея дня:*\n\n{trend}", parse_mode="Markdown", reply_markup=main_menu())
        return

    # НІША
    if text == "⚙️ Моя ніша":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("⚽ Football", "🌍 Mysterious Places")
        markup.add("💰 Money & Power", "🔒 Secret Organizations")
        markup.add("🧠 Psychology", "🔬 Science & Tech")
        markup.add("😂 Comedy", "💪 Motivation")
        bot.send_message(uid, "Обери свою нішу — бот запам'ятає і буде генерувати під неї:", reply_markup=markup)
        user_history[uid] = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": "waiting_niche"}]
        return

    niche_options = ["⚽ Football", "🌍 Mysterious Places", "💰 Money & Power", "🔒 Secret Organizations", "🧠 Psychology", "🔬 Science & Tech", "😂 Comedy", "💪 Motivation"]
    if text in niche_options and user_history.get(uid, [{}])[-1].get("content") == "waiting_niche":
        save_niche(uid, text)
        bot.send_message(uid, f"✅ Ніша збережена: *{text}*\nТепер всі сценарії будуть під твою аудиторію!", parse_mode="Markdown", reply_markup=main_menu())
        user_history[uid] = [{"role": "system", "content": SYSTEM_PROMPT}]
        return

    # КОНТЕНТ ПЛАН
    if text == "📅 Контент план на 7 днів":
        niche = get_niche(uid) or "general viral content"
        bot.send_message(uid, "⏳ Генерую контент план на 7 днів...")
        prompt = f"Create a 7-day content plan for YouTube Shorts in the niche: {niche}. For each day give: topic, hook idea, best time to post. Format it clearly day by day."
        add_to_history(uid, "user", prompt)
        reply = ask_groq(get_history(uid))
        add_to_history(uid, "assistant", reply)
        increment_generations(uid)
        bot.send_message(uid, f"📅 *Контент план на 7 днів:*\n\n{reply}", parse_mode="Markdown", reply_markup=main_menu())
        return

    # A/B ТЕСТ ХУКІВ
    if text == "🎯 A/B тест хуків":
        niche = get_niche(uid) or "viral content"
        bot.send_message(uid, "⏳ Генерую 3 варіанти хука...")
        prompt = f"Give me 3 completely different hook variations for a YouTube Short about {niche}. Label them A, B, C. Explain what makes each one work differently (curiosity vs shock vs controversy). Keep each hook under 15 words."
        add_to_history(uid, "user", prompt)
        reply = ask_groq(get_history(uid))
        add_to_history(uid, "assistant", reply)
        increment_generations(uid)
        bot.send_message(uid, f"🎯 *A/B тест хуків:*\n\n{reply}", parse_mode="Markdown", reply_markup=main_menu())
        return

    # АНАЛІЗ КАНАЛУ
    if text == "📊 Аналіз каналу":
        bot.send_message(uid, "📊 Опиши свій канал:\n\n— Ніша\n— Скільки підписників\n— Середні перегляди\n— Який контент постиш\n\nІ я дам конкретні поради як рости швидше!")
        return

    # ЯК ЗАРОБИТИ
    if text == "💰 Як заробити онлайн":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("📹 YouTube монетизація", "🎵 TikTok заробіток")
        markup.add("💼 Freelance з нуля", "🛍 Dropshipping")
        markup.add("◀️ Назад")
        bot.send_message(uid, "💰 Обери тему:", reply_markup=markup)
        return

    if text == "◀️ Назад":
        bot.send_message(uid, "Головне меню:", reply_markup=main_menu())
        return

    money_topics = {
        "📹 YouTube монетизація": "Give a complete step-by-step guide on how to monetize YouTube channel from 0. Include: how to get 1000 subscribers fast, what content works, how much money you can make, all monetization methods.",
        "🎵 TikTok заробіток": "Give a complete guide on making money on TikTok from 0. Include: TikTok creator fund, brand deals, live gifts, how to go viral, realistic income expectations.",
        "💼 Freelance з нуля": "Give a complete beginner guide to freelancing online. Include: best platforms (Fiverr, Upwork), what skills to offer, how to get first client, realistic income timeline.",
        "🛍 Dropshipping": "Give a complete beginner guide to dropshipping. Include: how it works, best platforms, how to find products, realistic costs and profits, common mistakes to avoid."
    }

    if text in money_topics:
        bot.send_message(uid, "⏳ Генерую гайд...")
        prompt = money_topics[text]
        add_to_history(uid, "user", prompt)
        reply = ask_groq(get_history(uid))
        add_to_history(uid, "assistant", reply)
        increment_generations(uid)
        bot.send_message(uid, reply, reply_markup=main_menu())
        return

    # ГЕНЕРАЦІЯ СЦЕНАРІЮ
    if text == "🎬 Згенерувати сценарій":
        niche = get_niche(uid)
        niche_text = f" для ніші {niche}" if niche else ""
        bot.send_message(uid, f"✍️ Напиши тему{niche_text} або просто напиши що хочеш і я згенерую вірусний сценарій!")
        return

    # ЧАТ З AI
    if text == "💬 Чат з AI":
        bot.send_message(uid, "💬 Пиши будь-що — я відповім! Можемо говорити про контент, заробіток, ідеї для відео або просто поспілкуємось 🤖")
        return

    # ЗАГАЛЬНИЙ ЧАТ
    bot.send_message(uid, "⏳ Думаю...")
    niche = get_niche(uid)
    if niche:
        user_msg = f"[User niche: {niche}] {text}"
    else:
        user_msg = text

    add_to_history(uid, "user", user_msg)
    try:
        reply = ask_groq(get_history(uid))
        add_to_history(uid, "assistant", reply)
        increment_generations(uid)
        bot.send_message(uid, reply, reply_markup=main_menu())
        bot.send_message(uid, "🔗 Поділись цим ботом з другом: @shortfypromt_bot")
    except Exception as e:
        bot.send_message(uid, f"❌ Помилка: {str(e)}")

# ===== ЗАПУСК =====
init_db()
threading.Thread(target=schedule_jobs, daemon=True).start()
bot.polling()
