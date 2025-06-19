import os
import logging
import requests
import json

from flask import Flask, request
import telebot
from buttons import menu_kb, role_kb, model_kb

TELEGRAM_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

user_roles = {}
user_model = {}

# Логгирование
logging.basicConfig(
    level=logging.INFO,
    filename='bot_errors.log',
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# === Telegram Handlers ===

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "👋 Добро пожаловать!\n\nПожалуйста, выберите пункт меню или напишите любое сообщение в чат чтобы начать общаться с ИИ:", reply_markup=menu_kb())

@bot.message_handler(commands=['role'])
def role_command(message):
    bot.send_message(message.chat.id, '🧠 Выберите роль, в которой бот будет отвечать:', reply_markup=role_kb())

@bot.message_handler(commands=['model'])
def model_command(message):
    bot.send_message(message.chat.id, '🤖 Выберите модель ИИ, с которой хотите общаться:', reply_markup=model_kb())

@bot.callback_query_handler(func=lambda call: call.data == "roles")
def role(call):
    bot.send_message(call.message.chat.id, '🧠 Выберите роль, в которой бот будет отвечать:', reply_markup=role_kb())

@bot.callback_query_handler(func=lambda call: call.data == "model")
def model(call):
    bot.send_message(call.message.chat.id, '🤖 Выберите модель ИИ, с которой хотите общаться:', reply_markup=model_kb())

@bot.callback_query_handler(func=lambda call: call.data.startswith('model_'))
def set_model(call):
    model_map = {
        "model_gpt4o": "openai/gpt-4o",
        "model_deepseek": "deepseek/deepseek-r1-0528-qwen3-8b:free",
        "model_gemini": "google/gemini-2.5-flash-preview-05-20"
    }
    model_id = model_map.get(call.data, "openai/gpt-4o")
    user_model[call.from_user.id] = model_id
    bot.send_message(call.message.chat.id, f'✅ Модель успешно выбрана: {model_id}\nТеперь напишите сообщение')

@bot.callback_query_handler(func=lambda call: call.data.startswith('role_'))
def set_role(call):
    role = call.data.replace('role_', '')
    user_roles[call.from_user.id] = role
    bot.send_message(call.message.chat.id, f"🎭 Роль установлена: {role}\nТеперь напишите сообщение.")

@bot.callback_query_handler(func=lambda call: call.data == "start")
def start_ai(call):
    prompt = "Привет! Что ты умеешь?"
    role = user_roles.get(call.from_user.id, "assistant")
    model = user_model.get(call.from_user.id, "openai/gpt-4o")
    ask_ai(call.message.chat.id, prompt, call.message, role, model)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    prompt = message.text
    role = user_roles.get(message.from_user.id, 'assistant')
    model = user_model.get(message.from_user.id, 'openai/gpt-4o')
    ask_ai(message.chat.id, prompt, message, role, model)

# === Обработка запроса к OpenRouter ===

def ask_ai(chat_id, prompt, message, role, model):
    system_roles = {
        'assistant': f"Ты дружелюбный помощник, который кратко и вежливо отвечает на вопросы. Имя пользователя {message.from_user.username}",
        'teacher': f"Ты строгий преподаватель, объясняющий с примерами. Имя пользователя {message.from_user.username}",
        'shutnik': f"Ты весёлый бот, который отвечает с юмором. Имя пользователя {message.from_user.username}"
    }
    system_msg = system_roles.get(role, "Ты просто помощник.")

    data = {
        "model": model,
        "max_tokens": 1000,
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": prompt}
        ]
    }

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            data=json.dumps(data),
            timeout=20
        )
        response.raise_for_status()
        reply = response.json()['choices'][0]['message']['content']
    except Exception as e:
        logging.exception(f"[AI ERROR] Ошибка: {e}")
        reply = "⚠️ Произошла ошибка при обработке запроса к ИИ."

    try:
        bot.send_message(chat_id, reply)
    except Exception as e:
        logging.exception(f"[SEND ERROR] Ошибка отправки сообщения: {e}")

# === Flask сервер для Webhook ===

@app.route(f'/{TELEGRAM_TOKEN}', methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
    bot.process_new_updates([update])
    return "ok", 200

@app.route('/', methods=['GET'])
def home():
    return 'Бот работает!'

# === Установка Webhook при запуске ===

if __name__ == "__main__":
    webhook_url = f"https://{os.getenv('RAILWAY_STATIC_URL')}/{TELEGRAM_TOKEN}"
    bot.remove_webhook()
    bot.set_webhook(url=webhook_url)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
