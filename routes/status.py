from aiogram import Router, types, F
from aiogram.filters.logic import or_f
from aiogram.filters import Command, CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
import logging


from keyboards.start import start_keyboard

from utils.pc import get_cpu_name, get_cpu_temp, get_cpu_usage ,get_ram_info , get_fan_speed ,get_disk_info , get_disk_health

__router__ = Router()



@__router__.message(F.text == "📊 Статистика сервера")
async def status_handler(message: Message):

    disks_text = ""

    for disk in get_disk_info():
        disks_text += (
            f"• {disk['device']} ({disk['mount']}): "
            f"{disk['used_gb']} GB / "
            f"{disk['total_gb']} GB "
            f"({disk['percent']}%)\n"
        )

    ram = get_ram_info()

    text = f"""
🖥️ <b>Статистика сервера</b>

🧠 <b>Процессор:</b>
Название: {get_cpu_name()}
Загруженность: {get_cpu_usage()}%
Температура: {get_cpu_temp()}

💾 <b>Оперативная память:</b>
Загруженность: {ram['used_gb']} GB / {ram['total_gb']} GB ({ram['percent']}%)

💽 <b>Диски:</b>
{disks_text}
"""

    await message.answer(text, parse_mode="HTML")