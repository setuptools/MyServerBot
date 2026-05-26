from aiogram import Router, types, F
from aiogram.filters.logic import or_f
from aiogram.filters import Command, CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
import logging


from keyboards.start import start_keyboard

__router__ = Router()



@__router__.message(CommandStart())
async def start_handler(message: Message):
    
    
    await message.answer("""
👋 <b>Привет!</b>

🤖Я <b>бот</b> которйы поможет тебе управлять твоим сервером из любой точки мира используя только <b>Telegram</b>. 
                         
<b>C помощью меня ты сможешь:</b>
• Управлять сервером
• Мониторить состояние сервера 
• Получать уведомления о важных событиях
• Управлять файлами на сервере
• Управлять процессами сервера 
         
""",
    reply_markup=await start_keyboard(), parse_mode="HTML")