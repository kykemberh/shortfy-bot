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

SYSTEM_PROMPT = """You are an expert viral content creator and online money-making coach targeting American audiences.

Your skills:
- Writing viral scripts in ENGLISH for YouTube Shorts, TikTok, Instagram Reels
- Analyzing YouTube channels and giving growth advice
- Teaching how to make money online: YouTube, TikTok, Freelance, Dropshipping
- Creating A/B hook tests, content plans, trending ideas

When generating scripts always include:
- [HOOK — 0-3 sec]
- [STORY — 3-33 sec]
- [CLOSING — 33-35 sec]
- 3 title options
- 10 hashtags

IMPORTANT: Always write scripts and content in ENGLISH. But if the user writes in Ukrainian, respond to them in Ukrainian, only keeping the actual script content in English.
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
    prompt = "Напиши коротку потужну ранкову мотивацію (3 речення) українською для творців контенту. Потім дай 1 конкретну пораду на сьогодні українською."
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
    prompt = "Яка ONE вірусна трендова тема зараз для YouTube Shorts яка отримає мільйони переглядів на американській аудиторії? Напиши назву теми та 2 речення чому вона трендова. Відповідь дай українською, але назву теми залиш англійською."
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
        "🎬 Генерую сценарії англійською\n"
        "📊 Аналізую твій канал\n"
        "💰 Вчу як заробляти онлайн\n"
        "🔥 Щодня нова трендова ідея\n\n"
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
        markup.add("⚽ Футбол", "🌍 Загадкові місця")
        markup.add("💰 Гроші та влада", "🔒 Секретні організації")
        markup.add("🧠 Психологія", "🔬 Наука та технології")
        markup.add("😂 Комедія", "💪 Мотивація")
        bot.send_message(uid, "Обери свою нішу — бот запам'ятає і генеруватиме під неї:", reply_markup=markup)
        users[uid]["waiting_niche"] = True
        return

    niche_options = ["⚽ Футбол", "🌍 Загадкові місця", "💰 Гроші та влада", "🔒 Секретні організації", "🧠 Психологія", "🔬 Наука та технології", "😂 Комедія", "💪 Мотивація"]
    if text in niche_options and users.get(uid, {}).get("waiting_niche"):
        users[uid]["niche"] = text
        users[uid]["waiting_niche"] = False
        bot.send_message(uid, f"✅ Ніша збережена: *{text}*\nТепер всі сценарії будуть під твою аудиторію!", parse_mode="Markdown", reply_markup=main_menu())
        return

    if text == "📅 Контент план на 7 днів":
        niche = users[uid].get("niche") or "загальний вірусний контент"
        bot.send_message(uid, "⏳ Генерую контент план на 7 днів...")
        prompt = f"Створи контент план на 7 днів для YouTube Shorts у ніші: {niche}. Для кожного дня дай: тему англійською, ідею хука англійською, найкращий час для публікації. Дні та пояснення напиши українською."
        add_to_history(uid, "user", prompt)
        reply = ask_groq(get_history(uid))
        add_to_history(uid, "assistant", reply)
        bot.send_message(uid, f"📅 *Контент план на 7 днів:*\n\n{reply}", parse_mode="Markdown", reply_markup=main_menu())
        return

    if text == "🎯 A/B тест хуків":
        niche = users[uid].get("niche") or "вірусний контент"
        bot.send_message(uid, "⏳ Генерую 3 варіанти хука...")
        prompt = f"Дай мені 3 абсолютно різних варіанти хука для YouTube Short про {niche}. Познач їх А, Б, В. Хуки пиши англійською (до 15 слів). Пояснення чому кожен працює — українською."
        add_to_history(uid, "user", prompt)
        reply = ask_groq(get_history(uid))
        add_to_history(uid, "assistant", reply)
        bot.send_message(uid, f"🎯 *A/B тест хуків:*\n\n{reply}", parse_mode="Markdown", reply_markup=main_menu())
        return

    if text == "📊 Аналіз каналу":
        bot.send_message(uid,
            "📊 Опиши свій канал і я дам конкретні поради як рости швидше:\n\n"
            "— Яка ніша?\n"
            "— Скільки підписників?\n"
            "— Середні перегляди?\n"
            "— Який контент постиш?\n\n"
            "Напиши і я проаналізую! 👇"
        )
        return

    if text == "💰 Як заробити онлайн":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("📹 YouTube монетизація", "🎵 TikTok заробіток")
        markup.add("💼 Freelance з нуля", "🛍 Dropshipping")
        markup.add("◀️ Назад")
        bot.send_message(uid, "💰 Обери тему і я дам покроковий гайд:", reply_markup=markup)
        return

    if text == "◀️ Назад":
        bot.send_message(uid, "Головне меню 👇", reply_markup=main_menu())
        return

    money_topics = {
        "📹 YouTube монетизація": "Дай повний покроковий гайд як монетизувати YouTube канал з нуля. Як швидко набрати 1000 підписників, який контент працює, скільки можна заробити. Відповідь українською.",
        "🎵 TikTok заробіток": "Дай повний гайд як заробляти на TikTok з нуля. TikTok creator fund, бренд-deals, подарунки в лайві, як стати вірусним. Відповідь українською.",
        "💼 Freelance з нуля": "Дай повний гайд для початківця по фрілансу онлайн. Кращі платформи, які навички пропонувати, як отримати першого клієнта. Відповідь українською.",
        "🛍 Dropshipping": "Дай повний гайд для початківця по дропшипінгу. Як це працює, кращі платформи, як знайти товари, реальні витрати і прибуток. Відповідь українською."
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
        bot.send_message(uid, f"✍️ Напиши тему{niche_text} і я згенерую вірусний сценарій англійською!")
        return

    if text == "💬 Чат з AI":
        bot.send_message(uid, "💬 Пиши будь-що українською — я відповім! Можемо говорити про контент, заробіток, ідеї для відео 🤖")
        return

    bot.send_message(uid, "⏳ Думаю...")
    niche = users[uid].get("niche")
    user_msg = f"[Ніша користувача: {niche}] {text}" if niche else text
    add_to_history(uid, "user", user_msg)
    try:
        reply = ask_groq(get_history(uid))
        add_to_history(uid, "assistant", reply)
        bot.send_message(uid, reply, reply_markup=main_menu())
        bot.send_message(uid, "🔗 Поділись ботом з другом: @shortfypromt_bot")
    except Exception as e:
        bot.send_message(uid, f"❌ Помилка: {str(e)}")

threading.Thread(target=schedule_jobs, daemon=True).start()
bot.polling()
