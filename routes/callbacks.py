from aiogram import Router, types, F
from aiogram.filters.logic import or_f
from aiogram.filters import Command, CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from aiogram.fsm.context import FSMContext 
import logging


from keyboards.start import start_keyboard


__router__ = Router()



@__router__.callback_query(F.data == "cancel")
async def cancel_callback_handler(cal: CallbackQuery, state: FSMContext):

    await state.clear()
    await cal.message.delete()
    await cal.message.answer("❌ Действие отменено", reply_markup=await start_keyboard())