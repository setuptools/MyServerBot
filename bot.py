import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import CallbackQuery


import os
import importlib
import sys

from utils.logger import Logger

from middleware.middleware import BotMiddleware

from config import TELEGRAM_TOKEN, ADMIN_IDS

# Логирование


class BotGroup(Bot):
    def __init__(self, token: str):
        super(BotGroup,self).__init__(token=token)

        self.dp = Dispatcher(storage=MemoryStorage())
        self.logger = Logger()

    async def load_route(self):
        for router in os.listdir("./routes"):
            
            if router.endswith(".py") and router != "__init__.py":
                module_name = f"routes.{router[:-3]}"
                module = importlib.import_module(module_name)
                if hasattr(module, "__router__"):
                    self.dp.include_router(module.__router__)
                    self.logger.info(f"Router loaded: {module_name}")
                else:
                    self.logger.warning(f"__router__ not found in {module_name}")
    

    async def load_middleware(self):
        self.dp.update.middleware(BotMiddleware(allowed_users=ADMIN_IDS,bot=self))
        self.logger.info("Middleware loaded")
    
    async def run(self):
        os.system("cls" if os.name == "nt" else "clear")
        
        # get me
        bot = await self.get_me()

        # load bot additions
        await self.load_route()
        await self.load_middleware()

        self.logger.info("Status work")
        self.logger.info(f"Bot: {bot.first_name} (@{bot.username})")

        await self.dp.start_polling(self)

if __name__ == '__main__':
    async def main():
    # Инициализация
        bot = BotGroup(token=TELEGRAM_TOKEN)
        await bot.run() 

    asyncio.run(main())
