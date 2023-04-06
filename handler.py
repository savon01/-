import re
import datetime
from telebot import types
from class_user import bot, user_base
from radapi import SearchHotel
from loguru import logger
from datetime import datetime


def checking_input_message(message: types.Message) -> None:
    """
    Проверка название города
    :param message: объект входящего сообщения от пользователя
    :return:
    """
    user = message.from_user.id
    chat = message.chat.id
    logger.info(f'Проверка сообщения введенного города')
    if len(re.findall(r'[А-Яа-яЁёa-zA-Z- ]+', message.text)) > 1 or message.text.startswith('/'):
        text_error = bot.send_message(user,
                                      'Название состоит из букв\n Повторите ввод')
        bot.register_next_step_handler(text_error, checking_input_message)
    else:
        user_base[user].language = checking_language(message.text)
        logger.info(f'Проверен язык сообщения {message.text}')
        user_base[user].search_city = message.text
        logger.info(f'Поиск города {message.text}')
        bot.register_next_step_handler(message, SearchHotel.search_city(bot=bot, message=message))


def checking_language(text: str) -> str:
    """
    Функция проверки языка
    :param text: текст города
    :return: 'ru_RU' или 'en_EN'
    """
    if re.findall(r'[А-ЯА-яЁё -]', re.sub(r'[- ]', '', text)):
        return 'ru_RU'
    else:
        return 'en_EN'


def checking_date1(message: types.Message) -> None:
    """
    Функция проверки введенной даты заезда в отель
    :param message: объект входящего сообщения от пользователя
    :return:
    """
    user = message.from_user.id
    chat = message.chat.id
    logger.info(f'Проверка даты')
    current_date = datetime.now().date()
    date_arrival = list(map(int, re.findall(r'\d+', message.text)))
    if not isinstance(message.text, str) or len(date_arrival) != 3 or date_arrival[0] > 31 or date_arrival[1] > 12 \
            or len(str(date_arrival[2])) != 4:
        err_num = bot.send_message(message.chat.id, 'Дата введена не верно!'
                                                    'Введите дату заезда в отель в формате (mm/dd/yyyy), '
                                                    '(не может быть меньше текущей даты)')
        bot.register_next_step_handler(err_num, checking_date1)
    else:
        date1 = datetime(date_arrival[2], date_arrival[1], date_arrival[0]).date()
        if date1 >= current_date:
            user_base[user].date_arrival = date1
            input_count_night = bot.send_message(chat, 'Введите дату выезда')
            bot.register_next_step_handler(input_count_night, checking_date2)
        else:
            err_num = bot.send_message(chat, 'Введите дату заезда в отель в формате (mm/dd/yyyy), '
                                                        '(не может быть меньше текущей даты)')
            bot.register_next_step_handler(err_num, checking_date1)


def checking_date2(message: types.Message) -> None:
    """
    Функция проверки введенной даты выезда из отеля
    :param message: объект входящего сообщения от пользователя
    :return:
    """
    user = message.from_user.id
    chat = message.chat.id
    logger.info(f'Проверка даты выезда')
    date_arrival = list(map(int, re.findall(r'\d+', message.text)))
    if not isinstance(message.text, str) or len(date_arrival) != 3 or date_arrival[0] > 31 or date_arrival[1] > 12 \
            or len(str(date_arrival[2])) != 4:
        err_num = bot.send_message(chat, 'Дата введена не верно!'
                                                    'Введите дату выезда из отеля в формате (mm/dd/yyyy), '
                                                    '(не может быть меньше даты заезда в отель)')
        bot.register_next_step_handler(err_num, checking_date2)
    else:
        date2 = datetime(date_arrival[2], date_arrival[1], date_arrival[0]).date()
        if date2 > user_base[user].date_arrival:
            user_base[user].date_of_departure = date2
            count_hotels = bot.send_message(chat,
                                            'Введите количество отелей (не более 25)')
            bot.register_next_step_handler(count_hotels, checking_numbers_of_hotels)
        else:
            err_num = bot.send_message(chat, 'Дата введена не верно!'
                                                        'Введите дату выезда из отеля в формате (mm/dd/yyyy), '
                                                        '(не может быть меньше даты заезда в отель)')
            bot.register_next_step_handler(err_num, checking_date2)


def request_photo(message: types.Message) -> None:
    """
    Функция выводит в чат кнопки для выбора поиска фото или нет
    :param message: объект входящего сообщения от пользователя
    :return:
    """
    user = message.from_user.id
    chat = message.chat.id
    logger.info(f'Вывод кнопок по фото')
    markup = types.InlineKeyboardMarkup()
    yes_photo = types.InlineKeyboardButton(text='Да', callback_data='yes')
    no_photo = types.InlineKeyboardButton(text='Нет', callback_data='no')
    markup.add(yes_photo, no_photo)
    bot.send_message(chat, 'Показать фотографии отелей?', reply_markup=markup)


def checking_numbers_of_hotels(message: types.Message) -> None:
    """
    Проверка ввода количества отелей.
    :param message: объект входящего сообщения от пользователя.
    :return:
    """
    user = message.from_user.id
    chat = message.chat.id
    logger.info(f'Проверка введенного числа количества отелей')
    if not isinstance(str(message.text), str) or not message.text.isdigit() or message.text.startswith('/'):
        err_num = bot.send_message(user,'Пожалуйста введите количество отелей с помощью цифр.'
                                        '\nКоличество не должно быть больше 25')
        bot.register_next_step_handler(err_num, checking_numbers_of_hotels)
    if int(message.text) > 25:
        user_base[user].count_hotels_to_display = 25
        bot.send_message(user,'Введенное число больше 25\nКоличество отлей заменено на 25')
        user_base[user].count_hotels_to_display = 25
    elif int(message.text) <= 25:
        user_base[user].count_hotels_to_display = int(message.text)

        if user_base[user].search_method == '/bestdeal':
            price = bot.send_message(user, 'Введите диапазон цен через любой разделитель в российских рублях'
                                           '\nНапример 100-5000')
            bot.register_next_step_handler(price, checking_price)
        else:
            request_photo(message)


def checking_price(message: types.Message) -> None:
    """
    Проверка диапазона цен отеля
    :param message: объект входящего сообщения от пользователя
    :return:
    """
    user = message.from_user.id
    chat = message.chat.id
    logger.info(f'Проверка цены по команде bestdeal')
    price_min_max = list(map(int, re.findall(r'\d+', message.text)))
    if not isinstance(message.text, str) or len(price_min_max) != 2 or message.text.startswith('/'):
        err_num = bot.send_message(chat, 'Введите диапазон цен через любой разделитель в российских рублях'
                                        '\nНапример 100-5000')
        bot.register_next_step_handler(err_num, checking_price)
    else:
        user_base[message.chat.id].price['min'] = min(price_min_max)
        user_base[message.chat.id].price['max'] = max(price_min_max)
        mcg_dict = bot.send_message(chat, 'Укажите диапазон расстояний от центра в {distance}. Пример 1-5'.format(
            distance='км'))
        bot.register_next_step_handler(mcg_dict, checking_distance)


def checking_distance(message: types.Message) -> None:
    """
    Проверка диапазона расстояний
    :param message: объект входящего сообщения от пользователя
    :return:
    """
    user = message.from_user.id
    chat = message.chat.id
    logger.info(f'Проверка расстояний по команде bestdeal')
    distance_min_max = list(map(int, re.findall(r'\d+', message.text)))

    if not isinstance(message.text, str) or len(distance_min_max) != 2 or message.text.startswith('/'):
        err_num = bot.send_message(chat,
                                   'Введите два число через любой разделитель')
        bot.register_next_step_handler(err_num, checking_distance)
    else:
        user_base[chat].distance['min'] = min(distance_min_max)
        user_base[chat].distance['max'] = max(distance_min_max)
        request_photo(message)


def checking_photo_count(message: types.Message) -> None:
    """
    Проверка введенного количества фото.
    :param message: объект входящего сообщения от пользователя.
    :return:
    """
    user = message.from_user.id
    chat = message.chat.id
    logger.info(f'Проверка введенного количесвта фото')
    if not isinstance(message.text, str) or not message.text.isdigit() or message.text.startswith('/'):
        err = bot.send_message(message.chat.id,
                               'Введите количество фотографий цифрами')
        bot.register_next_step_handler(err, checking_photo_count)
    else:
        if int(message.text) > 5:
            user_base[message.chat.id].count_photo = 5
            bot.send_message(message.chat.id, 'Введенное число больше 5. '
                             'Количество фото заменено на 5')
        else:
            user_base[message.chat.id].count_photo = int(message.text)
        SearchHotel.search_hotels(bot, message.chat.id)
