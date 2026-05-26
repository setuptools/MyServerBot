

from typing import List

from aiogram import BaseMiddleware, Bot
from aiogram.types import Message , CallbackQuery
from aiogram.handlers import BaseHandler

import logging
import time

from utils.logger import Logger


class BotMiddleware(BaseMiddleware):
    def __init__(self, allowed_users: List[int] = [],bot:Bot=None, *args , **kwargs) -> None:
        super(BotMiddleware).__init__()

        self.bot = bot
        self.logger = bot.logger
        self.allowed_users = allowed_users
        



    async def __call__(self, handler:BaseHandler, event, data):

        if event and event.message:
            msg:Message = event.message
            user = msg.from_user

            if user.id not in self.allowed_users:
                self.logger.warning(f"Unauthorized user - {user.username}({user.id})")
                return
            
            else:
                self.logger.info(f"message - {user.username}({user.id})")


        if event and event.callback_query:
            cb:CallbackQuery = event.callback_query
            user = cb.from_user

            if user.id not in self.allowed_users:
                self.logger.warning(f"Unauthorized user - {user.username}({user.id})")
                return
        
            else:
                self.logger.info(f"callback - {user.username}({user.id}) ")

                
        try:
            return await handler(event, data) 
        
        except Exception as err:
            self.logger.error(f"error - {err}")
