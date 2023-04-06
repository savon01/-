from peewee import CharField, SqliteDatabase, DateField, Model


bd = SqliteDatabase('base.bd')


class HistoryHotel(Model):
    col_user_id = CharField()
    col_comand = CharField()
    col_date = DateField()
    col_hotel = CharField()

    class Meta:
        database = bd
