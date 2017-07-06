from peewee import *
import newminisab

def copy():
    newminisab.db = SqliteDatabase('minisab.db')
    newminisab.db.connect()
    articles = [x for x in newminisab.article.select()]
    newminisab.db.close()

    newminisab.db = SqliteDatabase('../minisab.db')
    newminisab.db.connect()
    for x in articles:
        trouve = [y for y in newminisab.article.select(newminisab.article.guid).where(newminisab.article.guid == x.guid)]
        if len(trouve) == 0:
            print('title:', x.title)
    newminisab.db.close()
copy()