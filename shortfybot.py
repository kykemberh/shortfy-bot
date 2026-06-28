import telebot
import requests
import schedule
import threading
import time
from telebot import types

BOT_TOKEN = "8973743279:AAGk0bLOogSENf2weOGwwASSICG6EOYM4PE"
GROQ_KEY = "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"

bot = telebot.TeleBot(BOT_TOKEN)
users = {}
user_history = {}
daily_trend = {"trend": None}

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

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🎬 Згенерувати сценарій")
    markup.add("🔥 Трендова ідея дня", "📅 Контент план на 7 днів")
    markup.add("📊 Аналіз каналу", "🎯 A/B тест хуків")
    markup.add("💰 Як заробити онлайн", "⚙️ Моя ніша")
    markup.add("💬 Чат з AI")
    return markup

def send_daily_motivation():
    prompt = "Give a short powerful morning motivation (3 sentences) for content creators trying to grow online. Then give 1 specific actionable tip for today."
    try:
        msg = ask_groq([{"role": "user", "content": prompt}])
        for uid in list(users.keys()):
            try:
                bot.send_message(uid, f"🌅 Доброго ранку!\n\n{msg}\n\n🚀 Вперед до успіху!")
            except:
                pass
    except:
        pass

def generate_daily_trend():
    prompt = "What is ONE viral trending topic right now for YouTube Shorts that would get millions of views targeting American audience? Give topic name and 2 sentence explanation why it's trending."
    try:
        daily_trend["trend"] = ask_groq([{"role": "user", "content": prompt}])
    except:
        pass

def schedule_jobs():
    schedule.every().day.at("10:00").do(send_daily_motivation)
    schedule.every().day.at("08:00").do(generate_daily_trend)
    while True:
        schedule.run_pending()
        time.sleep(60)

@bot.message_handler(commands=['start'])
def start(message):
    uid = message.chat.id
    username = message.from_user.username or message.from_user.first_name
    if uid not in users:
        users[uid] = {"username": username, "niche": None}

    niche = users[uid]["niche"]
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
    if uid not in users:
        users[uid] = {"username": username, "niche": None}

    if text == "🔥 Трендова ідея дня":
        if not daily_trend["trend"]:
            bot.send_message(uid, "⏳ Генерую трендову ідею...")
            generate_daily_trend()
        bot.send_message(uid, f"🔥 *Трендова ідея дня:*\n\n{daily_trend['trend']}", parse_mode="Markdown", reply_markup=main_menu())
        return

    if text == "⚙️ Моя ніша":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("⚽ Football", "🌍 Mysterious Places")
        markup.add("💰 Money & Power", "🔒 Secret Organizations")
        markup.add("🧠 Psychology", "🔬 Science & Tech")
        markup.add("😂 Comedy", "💪 Motivation")
        bot.send_message(uid, "Обери свою нішу:", reply_markup=markup)
        users[uid]["waiting_niche"] = True
        return

    niche_options = ["⚽ Football", "🌍 Mysterious Places", "💰 Money & Power", "🔒 Secret Organizations", "🧠 Psychology", "🔬 Science & Tech", "😂 Comedy", "💪 Motivation"]
    if text in niche_options and users.get(uid, {}).get("waiting_niche"):
        users[uid]["niche"] = text
        users[uid]["waiting_niche"] = False
        bot.send_message(uid, f"✅ Ніша збережена: *{text}*", parse_mode="Markdown", reply_markup=main_menu())
        return

    if text == "📅 Контент план на 7 днів":
        niche = users[uid].get("niche") or "general viral content"
        bot.send_message(uid, "⏳ Генерую контент план...")
        prompt = f"Create a 7-day content plan for YouTube Shorts in the niche: {niche}. For each day give: topic, hook idea, best time to post."
        add_to_history(uid, "user", prompt)
        reply = ask_groq(get_history(uid))
        add_to_history(uid, "assistant", reply)
        bot.send_message(uid, reply, reply_markup=main_menu())
        return

    if text == "🎯 A/B тест хуків":
        niche = users[uid].get("niche") or "viral content"
        bot.send_message(uid, "⏳ Генерую 3 варіанти хука...")
        prompt = f"Give me 3 completely different hook variations for a YouTube Short about {niche}. Label them A, B, C. Keep each hook under 15 words."
        add_to_history(uid, "user", prompt)
        reply = ask_groq(get_history(uid))
        add_to_history(uid, "assistant", reply)
        bot.send_message(uid, reply, reply_markup=main_menu())
        return

    if text == "📊 Аналіз каналу":
        bot.send_message(uid, "📊 Опиши свій канал:\n\n— Ніша\n— Скільки підписників\n— Середні перегляди\n— Який контент постиш")
        return

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
        "📹 YouTube монетизація": "Give a complete step-by-step guide on how to monetize YouTube channel from 0.",
        "🎵 TikTok заробіток": "Give a complete guide on making money on TikTok from 0.",
        "💼 Freelance з нуля": "Give a complete beginner guide to freelancing online.",
        "🛍 Dropshipping": "Give a complete beginner guide to dropshipping."
    }

    if text in money_topics:
        bot.send_message(uid, "⏳ Генерую гайд...")
        add_to_history(uid, "user", money_topics[text])
        reply = ask_groq(get_history(uid))
        add_to_history(uid, "assistant", reply)
        bot.send_message(uid, reply, reply_markup=main_menu())
        return

    if text == "🎬 Згенерувати сценарій":
        niche = users[uid].get("niche")
        niche_text = f" для ніші {niche}" if niche else ""
        bot.send_message(uid, f"✍️ Напиши тему{niche_text}!")
        return

    if text == "💬 Чат з AI":
        bot.send_message(uid, "💬 Пиши будь-що — я відповім!")
        return

    bot.send_message(uid, "⏳ Думаю...")
    niche = users[uid].get("niche")
    user_msg = f"[User niche: {niche}] {text}" if niche else text
    add_to_history(uid, "user", user_msg)
    try:
        reply = ask_groq(get_history(uid))
        add_to_history(uid, "assistant", reply)
        bot.send_message(uid, reply, reply_markup=main_menu())
        bot.send_message(uid, "🔗 Поділись ботом: @shortfypromt_bot")
    except Exception as e:
        bot.send_message(uid, f"❌ Помилка: {str(e)}")

threading.Thread(target=schedule_jobs, daemon=True).start()
bot.polling()
