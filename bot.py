import telebot
import logging
import requests
import json
import time
from buttons import menu_kb, role_kb, model_kb

TELEGRAM_TOKEN = "7952352811:AAEqgtz9v94gFEWoFnLHiTEZYGI2Q7AJylQ"
OPENROUTER_API_KEY = "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"

bot = telebot.TeleBot(TELEGRAM_TOKEN)
bot.remove_webhook()

user_roles = {}
user_model = {}

# Логгирование ошибок
logging.basicConfig(
    level=logging.INFO,
    filename='bot_errors.log',
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s'
)

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    bot.send_message(user_id, "👋 Добро пожаловать!\n\nПожалуйста, выберите пункт меню или напишите любое сообщение в чат чтобы начать общаться с ИИ:", reply_markup=menu_kb())

@bot.message_handler(commands=['role'])
def role_command(message):
    user_id = message.from_user.id
    bot.send_message(user_id, '🧠 Выберите роль, в которой бот будет отвечать:', reply_markup=role_kb())

@bot.message_handler(commands=['model'])
def model_command(message):
    user_id = message.from_user.id
    bot.send_message(user_id, '🤖 Выберите модель ИИ, с которой хотите общаться:', reply_markup=model_kb())

@bot.callback_query_handler(func=lambda call: call.data == "roles")
def role(call):
    user_id = call.from_user.id
    bot.send_message(user_id, '🧠 Выберите роль, в которой бот будет отвечать:', reply_markup=role_kb())

@bot.callback_query_handler(func=lambda call: call.data == "model")
def model(call):
    user_id = call.from_user.id
    bot.send_message(user_id, '🤖 Выберите модель ИИ, с которой хотите общаться:', reply_markup=model_kb())

@bot.callback_query_handler(func=lambda call: call.data.startswith('model_'))
def set_model(call):
    user_id = call.from_user.id

    model_map = {
        "model_gpt4o": "openai/gpt-4o",
        "model_deepseek": "deepseek/deepseek-r1-0528-qwen3-8b:free",
        "model_gemini": "google/gemini-2.5-flash-preview-05-20"
    }

    model_id = model_map.get(call.data, "openai/gpt-4o")  # по умолчанию GPT-4o
    user_model[user_id] = model_id

    bot.send_message(user_id, f'✅ Модель успешно выбрана: {model_id}\nТеперь напишите сообщение')

@bot.callback_query_handler(func=lambda call: call.data.startswith('role_'))
def set_role(call):
    role = call.data.replace('role_', '')
    user_id = call.from_user.id
    user_roles[user_id] = role

    bot.send_message(user_id, f"🎭 Роль установлена: {role}\nТеперь напишите сообщение.")

@bot.callback_query_handler(func=lambda call: call.data == "start")
def start_ai(call):
    prompt = "Привет! Что ты умеешь?"
    user_id = call.from_user.id
    role = user_roles.get(user_id, "assistant")
    model = user_model.get(user_id, "openai/gpt-4o")

    ask_ai(call.message.chat.id, prompt, call.message, role, model)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    prompt = message.text
    user_id = message.from_user.id
    role = user_roles.get(user_id, 'assistant')
    model = user_model.get(user_id, 'openai/gpt-4o')
    ask_ai(message.chat.id, prompt, message, role, model)

def ask_ai(chat_id, prompt, message, role, model):
    user_id = message.from_user.id
    username = message.from_user.username

    system_roles = {
        'assistant': f"Ты дружелюбный помощник, который кратко и вежливо отвечает на вопросы. Имя пользователя {username}",
        'teacher': f"Ты строгий, умный преподаватель, объясняющий всё подробно и с примерами. Имя пользователя {username}",
        'shutnik': f"Ты весёлый бот, который на всё отвечает с юмором и шутками. Имя пользователя {username}"
    }

    system_msg = system_roles.get(role, f"Ты просто помощник. Имя пользователя {username}")

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
    except requests.exceptions.RequestException as e:
        logging.exception(f"[API ERROR] Ошибка соединения с OpenRouter для user_id {user_id}: {e}")
        bot.send_message(chat_id, f"❌ Ошибка при соединении с ИИ. Попробуйте позже.")
        return
    except Exception as e:
        logging.exception(f"[PARSE ERROR] Ошибка обработки ответа: {e}")
        reply = "⚠️ Произошла ошибка при обработке ответа от ИИ."

    try:
        bot.send_message(chat_id, reply)
    except Exception as e:
        logging.exception(f"[SEND ERROR] Не удалось отправить сообщение пользователю {user_id}: {e}")

if __name__ == '__main__':
    while True:
        try:
            bot.polling(none_stop=True, interval=0)
        except Exception as e:
            logging.exception(f"Произошла критическая ошибка: {e}")
            time.sleep(5)
