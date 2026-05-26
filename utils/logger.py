



from logging import getLogger, StreamHandler, Formatter, INFO

from colorama import Fore, init

class Logger:
    def __init__(self):
        super (Logger).__init__()

        init()

        self.logger = getLogger("MyPC")
        
        self.logger.setLevel(INFO)

        handler = StreamHandler()
        handler.setLevel(INFO)
        formatter = Formatter('[ %(asctime)s ]  %(message)s')
        handler.setFormatter(formatter)

        self.logger.addHandler(handler)

    

    def info(self, message: str):
        self.logger.info("[  " + Fore.GREEN + "OK" + Fore.RESET + "  ] " + message)

    def warning(self, message: str):
        self.logger.warning("[  " + Fore.YELLOW + "WARNING" + Fore.RESET + "  ] " + message)

    def error(self, message: str):
        self.logger.error("[  " + Fore.RED + "ERROR" + Fore.RESET + "  ] " + message)
    


