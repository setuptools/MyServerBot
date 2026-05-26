from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery, KeyboardButton , ReplyKeyboardMarkup





async def start_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard = [
            [KeyboardButton(text="📊 Статистика сервера"),KeyboardButton(text="⚡️ Диспетчер задач")],
            [KeyboardButton(text="📁 Файловый менеджер"),KeyboardButton(text="⌨️ Выполнить команду")],    
            [KeyboardButton(text="🔄 Перезапуск сервера")]
        ],
        resize_keyboard=True
    )
    return keyboard