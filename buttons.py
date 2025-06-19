from telebot import types

def menu_kb():
    kb = types.InlineKeyboardMarkup(row_width=3)

    but1 = types.InlineKeyboardButton('Начать общение с ИИ', callback_data='start')
    but2 = types.InlineKeyboardButton('Настроить роль ИИ', callback_data='roles')
    but3 = types.InlineKeyboardButton('Выбрать модель ИИ', callback_data='model')

    kb.add(but1, but2, but3)

    return kb

def role_kb():
    kb = types.InlineKeyboardMarkup(row_width=3)

    but1 = types.InlineKeyboardButton('Ассистент', callback_data='role_assistant')
    but2 = types.InlineKeyboardButton('Учитель', callback_data='role_teacher')
    but3 = types.InlineKeyboardButton('Шутник', callback_data='role_shutnik')

    kb.add(but1, but2, but3)

    return kb

def model_kb():
    kb = types.InlineKeyboardMarkup(row_width=3)

    but1 = types.InlineKeyboardButton('Gpt 4o', callback_data='model_gpt4o')
    but2 = types.InlineKeyboardButton('DeepSeek', callback_data='model_deepseek')
    but3 = types.InlineKeyboardButton('Gemini', callback_data='model_gemini')

    kb.add(but1, but2, but3)

    return kb