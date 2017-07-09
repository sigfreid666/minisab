from peewee import *
import newminisab

olddb = SqliteDatabase('minisabold.db')

ct_categorie_sabnzbd = [('*', []),
                        ('livre', ['Ebook']),
                        ('logiciel', ['Autres OS']),
                        ('romance', []),
                        ('anime', ['Anime HD']),
                        ('musique', ['Mp3', 'Vidéo Zik', 'DVD Zik']),
                        ('serietv', []),
                        ('documentaire', ['Docs / Actu', 'Emissions']),
                        ('film', ['Films HD'])]


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
    lu = BooleanField(index=True, default=False)
    annee = IntegerField(default=0)

    def calculer_categorie_favoris(self, categorie):
        categorie_sabnzbd = '*'
        for x in ct_categorie_sabnzbd:
            if categorie in x[1]:
                categorie_sabnzbd = x[0]
        return categorie_sabnzbd

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
        ar.lu = self.lu
        ar.annee = self.annee
        try:
            ar.categorie = newminisab.categorie.get(newminisab.categorie.nom == self.categorie)
        except newminisab.categorie.DoesNotExist:
            ar.categorie = newminisab.categorie(nom=self.categorie)
            ar.categorie.categorie_sabnzbd = self.calculer_categorie_favoris(ar.categorie.nom)
            ar.categorie.save()
        return ar

    class Meta:
        database = olddb


class recherche(Model):
    id_check = IntegerField(unique=True)
    url = CharField()
    taille = CharField()
    title = CharField()
    id_sabnzbd = CharField(default='')
    categorie_sabnzbd = CharField(default='')
    article = ForeignKeyField(article, related_name='recherche_resultat')

    def convertold(self):
        ar = newminisab.recherche()
        ar.id_check = self.id_check
        ar.url = self.url
        ar.taille = self.taille
        ar.title = self.title
        ar.id_sabnzbd = self.id_sabnzbd
        ar.fichier = self.article.fichier
        ar.article = self.article
        return ar

    class Meta:
        database = olddb


def convert():
    olddb.connect()
    newminisab.db.connect()
    newminisab.db.create_tables([newminisab.article,
                                 newminisab.recherche,
                                 newminisab.categorie], safe=True)
    for y in [ article, recherche ]:
        for x in y.select():
            y = x.convertold()
            y.save()
    newminisab.db.close()
    olddb.close()


convert()
