from peewee import *
import newminisab

olddb = SqliteDatabase('minisabold.db')


class article(Model):
    title = CharField()
    link = CharField()
    description = CharField()
    pubDate = CharField()
    comment = CharField()
    guid = IntegerField()
    meta = CharField()
    nfo = CharField()
    fichier = CharField()
    taille = CharField()
    categorie = CharField()

    def convertold(self):
        ar = newminisab.article()
        ar.title = self.title
        ar.link = self.link
        ar.description = self.description
        ar.pubDate = self.pubDate
        ar.comment = self.comment
        ar.guid = self.guid
        ar.meta = self.meta
        ar.nfo = self.nfo
        ar.fichier = self.fichier
        ar.taille = self.taille
        ar.categorie = self.categorie
        return ar

    class Meta:
        database = olddb


def convert():
    olddb.connect()
    newminisab.db.connect()
    newminisab.db.create_tables([newminisab.article], safe=True)
    for x in article.select():
        y = x.convertold()
        y.save()
    newminisab.db.close()
    olddb.close()


convert()
