import re
from handler import checking_input_message, checking_photo_count, checking_date1
from class_user import bot, user_base, Users
from telebot import types
from loguru import logger
from telebot.types import CallbackQuery
from radapi import SearchHotel
from history import show_history
from datetime import datetime


coman = '/lowprice- найти самые дешёвых отели в городе,\n' \
         '/heghprice- найти самые дорогие отелей в городе,\n' \
         '/bestdeal- найти наиболее подходящих по цене и расположению от центра.\n' \
         '/history- по команде "История" — вывожу историю поиска отелей на экран.\n' \
        '/help- по команде "Помощь" расскажу что я могу'


@bot.message_handler(commands=['start', 'lowprice', 'heghprice', 'bestdeal', 'history', 'help'])
def handler_start(message: types.Message):
    """
    Функция обработки входящего сообщений: /start
    :param message: объект входящего сообщения от пользователя
    :type: type.Message
    """
    user = message.from_user.id
    logger.info(f'Введена команда {message.text}')
    if not user_base.get(user):
        user_base[user] = Users(message)
    if message.text == '/start':
        bot.send_message(user, f'Приветствую Вас!!! Я Бот по поиску отелей! Вот что я могу : \n {coman}')
    elif message.text in ['/lowprice', '/heghprice', '/bestdeal']:
        user_base[user].date_comand = datetime.today().strftime("%d.%m.%Y")
        user_base[user].time_comand = datetime.today().strftime("%H:%M:%S")
        if message.text == '/lowprice':
            user_base[user].search_method = 'PRICE'
        elif message.text == '/heghprice':
            user_base[user].search_method = 'PRICE_HIGHEST_FIRST'
        else:
            user_base[user].search_method = '/bestdeal'
        city = bot.send_message(user, 'Введите город для поиска')
        bot.register_next_step_handler(city, checking_input_message)
    elif message.text == '/history':
        show_history(message)
    elif message.text == '/help':
        bot.send_message(user, f'Я Бот по поиску отелей! Вот что я могу: \n {coman}')


@bot.message_handler(content_types='text')
def soob(message: types.Message):
    user = message.from_user.id
    bot.send_message(user, f'Я Вас не понимаю! Вот мои команды: \n {coman}')


@bot.callback_query_handler(func=lambda button_result: True)
def buttons_inl(button_result: CallbackQuery):
    """
    Функция-обработчик после нажатия кнопок пользователем
    :param button_result: response объекта при нажатии кнопок пользователем
    :return:
    """
    result = button_result.message.chat.id
    if button_result.data.startswith('_choice_city_'):
        city = int(re.sub(r'_choice_city_', '', button_result.data))
        user_base[result].id_city = \
            user_base[result].cache_data['suggestions'][0]['entities'][city][
                        'destinationId']
        bot.delete_message(result, button_result.message.message_id)
        date1 = bot.send_message(result, 'Введите дату заезда в отель в формате (mm/dd/yyyy)'
                                                                '(не может быть меньше текущей даты)')
        bot.register_next_step_handler(date1, checking_date1)

    elif button_result.data in ['yes', 'no']:
        user_base[result].photo = (True if button_result.data == 'yes' else False)
        bot.delete_message(result, button_result.message.message_id)
        if user_base[result].photo:
            photo = bot.send_message(result,
                                     'Введите количество фотографий (максимум 5)')
            bot.register_next_step_handler(photo, checking_photo_count)
        else:
            user_id = result
            SearchHotel.search_hotels(bot, user_id)


bot.infinity_polling()
