import os
from telebot import TeleBot
from dotenv import load_dotenv
from loguru import logger


load_dotenv()
TOKEN = os.getenv("TELEGRAM_API_TOKEN")
bot = TeleBot(TOKEN)
logger.info('Бот запустился')
user_base = dict()


class Users:

    def __init__(self, user):
        self.user_id: int = user.from_user.id
        self.search_method = None
        self.search_city = None
        self.language = 'ru-RU'
        self.id_city = None
        self.count_hotels_to_display: None
        self.price: dict = dict()
        self.distance: dict = dict()
        self.photo = None
        self.count_photo = None
        self.cache_data = None
        self.date_arrival = None
        self.date_of_departure = None
        self.date_comand = None
        self.time_comand = None
        self.date = None

    def clear_cache(self) -> None:
        """Функция для очистки кэша атрибута поиска"""
        self.search_method = None
        self.search_city = None
        self.cache_data = None
        self.date_arrival = None
        self.language = 'ru-RU'