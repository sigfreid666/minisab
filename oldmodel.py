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
    favorie = BooleanField(index=True, default=False)
    sabnzbd = CharField(default='')
    recherche = CharField(default='')

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
        ar.favorie = self.favorie
        
        return ar

    class Meta:
        database = olddb


class recherche(Model):
    id_check = IntegerField(unique=True)
    url = CharField()
    taille = CharField()
    title = CharField()
    article = ForeignKeyField(article, related_name='recherche_resultat')

    def convertold(self):
        ar = newminisab.recherche()
        ar.id_check = self.id_check
        ar.url = self.url
        ar.taille = self.taille
        ar.title = self.title
        ar.article = self.article

    class Meta:
        database = olddb


def convert():
    olddb.connect()
    newminisab.db.connect()
    newminisab.db.create_tables([newminisab.article,
                                 newminisab.recherche], safe=True)
    for y in [ article, recherche ]:
        for x in y.select():
            y = x.convertold()
            y.save()
    newminisab.db.close()
    olddb.close()


convert()
