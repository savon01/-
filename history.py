from telebot import types
from class_user import bot, user_base
from models import *


def save_history(user_id: int) -> None:
    """
    Функция сохраняет историю запросов пользователей
    :param user_id: ID пользователя
    :return:
    """
    history = []
    for element in user_base[user_id].cache_data['data']['body']['searchResults']['results']:
        name = element['name'],
        address = element['address'].get('countryName'),
        address_locatity = element['address'].get('locality'),
        street_address = element['address'].get('streetAddress') if element['address'].get('streetAddress') else "",
        price = element['ratePlan']['price']['current']
        hotels = (name, address, address_locatity, street_address, price)
        history.append(hotels)

    if user_base[user_id].search_method == 'PRICE':
        comand = '/lowprice'
    elif user_base[user_id].search_method == 'PRICE_HIGHEST_FIRST':
        comand = '/heghprice'
    else:
        comand = '/bestdeal'
    with bd:
        bd.create_tables([HistoryHotel])
        HistoryHotel(col_user_id='{}'.format(user_id),
                     col_date='{}, {}'.format(user_base[user_id].date_comand, user_base[user_id].time_comand),
                     col_comand='{}'.format(comand),
                     col_hotel='{}'.format(history)).save()


def show_history(message: types.Message) -> None:
    """
    Функция выводит историю на экран пользователю
    :param message: объект входящего сообщения от пользователя
    :return:
    """
    with bd:
        try:
            history_mess = ''
            user_history = HistoryHotel.select().where(HistoryHotel.col_user_id == message.from_user.id)
            if user_history:
                for i in user_history:
                    history_mess += '\n' + str(i.col_date)
                    history_mess += '\nМетод поиска: ' + i.col_comand
                    hotels = ''
                    for info in eval(i.col_hotel):
                        name = info[0]
                        country = info[1]
                        city = info[2]
                        street = info[3]
                        price = info[4]
                        hotels += f'\n{name}\n{country}, {city}, {street}\n Цена: {price}'
                    history_mess += hotels + '\n'
                bot.send_message(message.chat.id, history_mess)
        except:
            bot.send_message(message.chat.id, 'История пуста')
