import requests
from peewee import *
import html.parser
import re
import logging
import itertools
from indexeur import recherche_indexeur
import click
from settings import dbfile,logfile
from functools import wraps

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# create a file handler
handler = logging.FileHandler(logfile, encoding='utf-8')
handler.setLevel(logging.DEBUG)

# create stderr handler
handlerstd = logging.StreamHandler()
handlerstd.setLevel(logging.INFO)

# create a logging format
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# add the handlers to the logger
logger.addHandler(handler)
logger.addHandler(handlerstd)
#logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', 
#                    filename='/var/services/homes/admin/minisab/minisab.log', 
#                    level=logger.info)

db = SqliteDatabase(dbfile)


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

    def analyse_description(self):
        logger.debug('analyse_description : debut')
        meta = {}
        for x in self.description.split('<br>'):
            data = x.strip()
            logger.debug('analyse_description : champs <%s>', data)
            # detection lien
            if data.startswith('<a href'):
                reg = re.match(r'<a[ ]*href="(.*)">[ ]*Fichier Nfo[ ]*</a>', data)
                logger.debug('analyse_description : lien detecte %s', str(reg))
                if reg is not None:
                    self.nfo = reg.groups()[0]
                    # r = requests.get(self.nfo)
                    # self.nfo_html = r.text
            else:
                decoup = [y.strip() for y in data.strip().split(':')]
                logger.debug('analyse_description : split champs %s', str(decoup))
                if decoup[0] == 'Nom du fichier':
                    self.fichier = decoup[1]
                elif decoup[0] == 'Taille':
                    self.taille = decoup[1]
                elif decoup[0] == 'Catégorie':
                    self.categorie = decoup[1]
                elif len(decoup) == 2:
                    meta[decoup[0]] = decoup[1]
        self.meta = str(meta)
        logger.debug('analyse_description : fin')

    def lancer_recherche(self):
        ret = recherche_indexeur('https://binsearch.info/?q={0}&max=100',
                                 self.fichier)
        if len(ret) > 0:
            for item in ret:
                logger.info('item %s', str(item))
                try:
                    rec = recherche(id_check=item['id'],
                                    url=item['url'],
                                    taille=item['taille'] if 'taille' in item else 'Vide',
                                    title=item['title'],
                                    article=self)
                    rec.save()
                except IntegrityError:
                    logger.error('recherche_indexeur : item deja existant <%s>', item['id'])

    def categorie_preferee(self):
        return (not self.favorie) and (self.categorie in categorie_preferee)

    def categorie_autre(self):
        return (not self.favorie) and (self.categorie not in categorie_preferee)

    def __str__(self):
        return '<%s %s %s>' % (self.title, self.pubDate, self.favorie)

    def printall(self):
        return ('<' + '<' + str(self.title) + '>,\n' +
                '<' + str(self.link) + '>,\n' +
                '<' + str(self.description) + '>,\n' +
                '<' + str(self.pubDate) + '>,\n' +
                '<' + str(self.comment) + '>,\n' +
                '<' + str(self.guid) + '>,\n' +
                '<' + str(self.meta) + '>,\n' +
                '<' + str(self.nfo) + '>,\n' +
                '<' + str(self.fichier) + '>,\n' +
                '<' + str(self.taille) + '>,\n' +
                '<' + str(self.categorie) + '>,\n' +
                '<' + str(self.favorie) + '>,\n' +
                '<' + str(self.sabnzbd) + '>,\n' +
                '<' + str(self.recherche) + '>')

    class Meta:
        database = db


class recherche(Model):
    id_check = IntegerField(unique=True)
    url = CharField()
    taille = CharField()
    title = CharField()
    article = ForeignKeyField(article, related_name='recherche_resultat')

    class Meta:
        database = db


class ParserArticle(html.parser.HTMLParser):

    def resetin(self):
        self.data = []
        self.tag = None
        self.ondata = False

    def handle_starttag(self, tag, attr):
        if tag == 'item':
            logger.debug('ParserArticle.handle_starttag : nouvel item')
            self.data.append(article(link='', description='', pubDate='', comment='',
                                     fichier='', taille='', nfo='', meta=''))
            self.ondata = True
        else:
            self.tag = tag
            logger.debug('ParserArticle.handle_starttag : nouveau tag <%s>', tag)

    def handle_endtag(self, tag):
        self.tag = None
        if tag == 'item':
            self.ondata = False
            self.data[-1].analyse_description()

    def handle_data(self, data):
        if self.ondata and (self.tag is not None):
            self.data[-1].__setattr__(self.tag, data)
            logger.debug('ParserArticle.handle_data : attribut <%s> <%s>', self.tag, data)


def base_de_donnee(wrap):
    @wraps(wrap)
    def wrapper():
        global db
        try:
            db.connect()
            db.create_tables([article, recherche], safe=True)
        except OperationalError:
            pass
        ret = wrap()
        db.close()
        return ret
    return wrapper

@click.group()
def cli():
    pass

@cli.command('check')
@base_de_donnee
def check_new_article():
    myurl = "http://www.binnews.in/rss/rss_new.php"
    logger.info('check_new_article: debut url <%s>', myurl)
    r = requests.get(myurl)
    logger.info('check_new_article: fin requete status <%d> content-type <%s>',
                r.status_code, r.headers['content-type'])
    resultat = r.text
    logger.debug('check_new_article: taille reponse <%d>', len(resultat))
    parse = ParserArticle()
    parse.resetin()
    parse.feed(resultat)
    logger.info('check_new_article: article detecte <%d>', len(parse.data))
    nb_nouveau_article = 0
    for x in parse.data:
        try:
            ar = article.get(article.guid == x.guid)
            logger.debug('check_new_article: article existant <%s>', ar.guid)
        except article.DoesNotExist:
            x.save()
            logger.debug('check_new_article: nouvel article <%s>', x.title)
            nb_nouveau_article = nb_nouveau_article + 1
    logger.info('check_new_article: %d nouveau(x) article(s)', nb_nouveau_article)


@base_de_donnee
def recuperer_tous_articles():
    return [x for x in article.select()]


@base_de_donnee
def recuperer_tous_articles_par_categorie():
    favoris = [x for x in article.select().where(article.favorie == True)]
    a = [x for x in article.select().where(article.favorie == False)]
    a.sort(key=lambda x: x.categorie)
    b = itertools.groupby(a, lambda x: x.categorie)
    c = {x: [z for z in y] for x, y in b}
    return (c, favoris)


if __name__ == "__main__":
    cli()
