import os
import json
import re
import requests
from class_user import user_base
from telebot import types, apihelper
from class_user import bot
from loguru import logger
from history import save_history

RAPID_API_TOKEN = os.getenv("RAPID_API_TOKEN")


class SearchHotel:
    """
    Класс информации получаемой от requests.
    """
    headers = {
        'x-rapidapi-key': RAPID_API_TOKEN,
        'x-rapidapi-host': "hotels4.p.rapidapi.com"
    }

    @classmethod
    def search_city(cls, bot, message: types.Message) -> None:
        """Функция отправляет запрос на сервер для получения информации
        уточняет искаемый город, записывает информацию в кэш объекта User
        отправляет список городов в виде кнопок.
        :param bot: объект телеграмм бота.
        :param message: объект входящего сообщения от пользователя
        """
        logger.info('поиск города')
        url = "https://hotels4.p.rapidapi.com/locations/v2/search"
        querystring = {"query": message.text, 'locale': user_base[message.chat.id].language}
        bot.send_message(message.chat.id, 'Идет поиск похожих городов')
        try:
            response = requests.request('GET', url, headers=cls.headers, params=querystring, timeout=25)
            user_base[message.from_user.id].cache_data = json.loads(response.text)
            patterns_span = re.compile(r'<.*?>')
            cls.generation_buttons_list_for_city_clarification(bot=bot, message=message, patterns=patterns_span)
        except requests.exceptions.ReadTimeout:
            bot.send_message(message.from_user.id, 'Возникла ошибка при поиске. Попробуйте позднее')

    @classmethod
    def generation_buttons_list_for_city_clarification(cls, bot, message: types.Message, patterns: re.Pattern) -> None:
        """
        Функция составляет и отправляет в чат список городов в случае нахождения
        :param bot: объект телеграмм бота
        :param message: объект входящего сообщения от пользователя
        :param patterns: class 're.Pattern'
        :return:
        """
        logger.info('Похожие города')
        if user_base[message.chat.id].cache_data['suggestions'][0]['entities']:
            markup = types.InlineKeyboardMarkup()
            count = 0
            for entities_city in user_base[message.from_user.id].cache_data['suggestions'][0]['entities']:
                add = types.InlineKeyboardButton(text=patterns.sub('', entities_city['caption']),
                                                 callback_data=f'_choice_city_{count}',)
                markup.add(add)
                count += 1
            bot.send_message(message.from_user.id, 'Уточните город', reply_markup=markup)
        else:
            bot.send_message(message.from_user.id, 'По данному городу данных нет.')

    @classmethod
    def search_hotels(cls, bot, user_id: int) -> None:
        """Функция поиска отелей по выбранным параметрам метода поиска
        :param bot: объект телеграмм бота
        :param user_id: int id пользователя
        """
        logger.info('Поиск отелей')
        url = "https://hotels4.p.rapidapi.com/properties/list"
        querystring = {"destinationId": user_base[user_id].id_city,
                       "pageNumber": "1",
                       "pageSize": f"{user_base[user_id].count_hotels_to_display}",
                       "checkIn": user_base[user_id].date_arrival,
                       "checkOut": user_base[user_id].date_of_departure,
                       "adults1": "1",
                       "sortOrder": user_base[user_id].search_method,
                       "locale": user_base[user_id].language,
                       "currency": "RUB",
                       "landmarkIds": "city center"}

        if user_base[user_id].search_method == '/bestdeal':
            querystring.update({'price_min': user_base[user_id].price['min'],
                                'price_max': user_base[user_id].price['max'],
                                'sortOrder': 'PRICE',
                                'landmarkIds': 'city center'}
                               )

        try:
            sys_message = bot.send_message(user_id, 'Идет поиск......')
            responce = requests.get(url, headers=cls.headers, params=querystring, timeout=25)
            user_base[user_id].cache_data = json.loads(responce.text)
            apihelper.delete_message(os.getenv("TELEGRAM_API_TOKEN"), sys_message.chat.id,
                                     sys_message.id)
            cls.show_hotels(user_id)
        except requests.exceptions.ReadTimeout:
            bot.send_message('Возникла ошибка при поиске. Попробуйте позднее')

    @classmethod
    def show_hotels(cls, user_id: int) -> None:
        """Функция собирает информацию из спарсинного кэша подготовленные совпадения
        собирает список фотографий если нужно
        отправляет в чат подготовленные сообщение
        :param user_id: id пользователя
        """
        logger.info('Вывод отелей')
        url = "https://hotels4.p.rapidapi.com/properties/get-hotel-photos"
        best_deal = 0
        for i in user_base[user_id].cache_data['data']['body']['searchResults']['results']:
            if user_base[user_id].distance and user_base[user_id].search_method == '/bestdeal':
                min_dist = user_base[user_id].distance.get('min')
                max_dist = user_base[user_id].distance.get('max')
                dist_center = int(re.findall(r'\d+', i["landmarks"][0]["distance"])[0])
                if not min_dist <= dist_center <= max_dist:
                    continue
                else:
                    best_deal += 1
                    if best_deal > user_base[user_id].count_hotels_to_display:
                        break
            price_count = list(map(int, re.findall(r'\d+', i['ratePlan']['price']['current'])))
            price_count = float(".".join(map(str, price_count))) * \
                          (user_base[user_id].date_of_departure - user_base[user_id].date_arrival).days
            i_text = '*Название: {name}*\n*Адрес: {address}, {address_locatity}, {street_address}*\n' \
                     '*От центра грода : {distance}*\n*Цена: {price}*\n*Цена за весь период: {prices} RUB*\n'.\
                format(
                name=i['name'],
                address=i['address'].get('countryName'),
                address_locatity=i['address'].get('locality'),
                street_address=i['address'].get('streetAddress')
                if i['address'].get('streetAddress')
                else "",
                distance=i["landmarks"][0]["distance"],
                price=i['ratePlan']['price']['current'],
                prices=round(price_count, 3)
                )

            if user_base[user_id].photo:
                sys_message = bot.send_message(user_id, f'Идет поиск фото отеля *{i["name"]}*')
                response = requests.get(url, headers=cls.headers, params={'id': i['id']})
                data = json.loads(response.text)
                if data:
                    photo_list = [
                        types.InputMediaPhoto(data['hotelImages'][0]['baseUrl'].format(size='w'),
                                              caption=i_text + "https://hotels.com/ho{hotel_id}".format(hotel_id=i['id']),
                                              parse_mode='Markdown')
                    ]
                    if len(data['hotelImages']) < user_base[user_id].count_photo:
                        count_photo = len(data['hotelImages'])
                    else:
                        count_photo = user_base[user_id].count_photo
                    if count_photo > 1:
                        for index in range(1, count_photo):
                            photo_list.append(
                                types.InputMediaPhoto(data['hotelImages'][index]['baseUrl'].format(size='w')))
                    bot.send_media_group(user_id, photo_list)
                    apihelper.delete_message(os.getenv("TELEGRAM_API_TOKEN"), sys_message.chat.id, sys_message.id)
                    photo_list.clear()
            else:
                bot.send_message(user_id, i_text + "https://hotels.com/ho{hotel_id}".format(hotel_id=i['id']))
        if best_deal == 0 and user_base[user_id].search_method == '/bestdeal':
            bot.send_message(user_id, 'Подходящих отелей не найдено')
        save_history(user_id)
        bot.send_message(user_id, 'Поиск завершен!')
