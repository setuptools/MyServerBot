from aiogram import Router, types, F, Bot
from aiogram.filters.logic import or_f
from aiogram.filters import Command, CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import logging

from utils.command import SecureCommandExecutor

from keyboards.start import start_keyboard


__router__ = Router()





class CommandState(StatesGroup):
    cmd = State()

    message_id = State()


@__router__.message(F.text == "⌨️ Выполнить команду")
async def command_handler(message: Message, state: FSMContext):
    

    _mes = await message.answer("Введите команду для выполнения на сервере (или нажмите кнопку ниже для отмены):", 
                         reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                             [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")]
                         ]))
    
    await state.update_data(message_id=_mes.message_id)
    await state.set_state(CommandState.cmd)


@__router__.message(CommandState.cmd)
async def execute_command_handler(message: Message, state: FSMContext, bot:Bot):
    cmd = message.text

    data = await state.get_data()

    await message.delete()
    await bot.delete_message(chat_id=message.chat.id, message_id=data['message_id'])

    executer = SecureCommandExecutor()
    output = executer.execute(cmd)


    result = f"""
📟 Команда: {cmd}
✅ Статус: {output.status.value}
🖨️ Результат: {output.output}

"""  
    if output.error:
        result += f"❌ Ошибка: {output.error}"

    await message.answer(result, reply_markup=await start_keyboard())
    await state.clear()
    
