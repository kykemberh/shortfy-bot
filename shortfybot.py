import telebot
import requests
from telebot import types

BOT_TOKEN = "8973743279:AAGk0bLOogSENf2weOGwwASSICG6EOYM4PE"
GROQ_KEY = "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"

bot = telebot.TeleBot(BOT_TOKEN)

def ask_groq(topic):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{
            "role": "user",
            "content": f"""Write a viral YouTube Shorts script (35 sec) in English about: {topic}

Format:
[HOOK — 0-3 sec] — shocking opening line
[STORY — 3-33 sec] — escalating facts, short sentences
[CLOSING — 33-35 sec] — powerful ending

Style: short sentences, shocking facts, no filler."""
        }]
    }
    response = requests.post(url, headers=headers, json=payload)
    data = response.json()
    return data["choices"][0]["message"]["content"]

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("⚽ Football", "🌍 Mysterious Places")
    markup.add("💰 Money & Power", "🔒 Secret Organizations")
    markup.add("🏆 Champions League", "✍️ Своя тема")
    bot.send_message(message.chat.id, "Привіт! Обери тему для YouTube Shorts:", reply_markup=markup)

@bot.message_handler(func=lambda m: True)
def generate(message):
    if message.text == "✍️ Своя тема":
        bot.send_message(message.chat.id, "Напиши свою тему:")
        return
    bot.send_message(message.chat.id, "⏳ Генерую сценарій...")
    try:
        script = ask_groq(message.text)
        bot.send_message(message.chat.id, script)
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Помилка: {str(e)}")

bot.polling()
