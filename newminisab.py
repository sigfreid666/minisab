import requests
from peewee import *
import html.parser
import re
import logging
import itertools

logging.basicConfig(level=logging.INFO)

db = SqliteDatabase('minisab.db')


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

    def analyse_description(self):
        logging.info('analyse_description : debut')
        meta = {}
        for x in self.description.split('<br>'):
            data = x.strip()
            logging.info('analyse_description : champs <%s>', data)
            # detection lien
            if data.startswith('<a href'):
                reg = re.match(r'<a[ ]*href="(.*)">[ ]*Fichier Nfo[ ]*</a>', data)
                logging.info('analyse_description : lien detecte %s', str(reg))
                if reg is not None:
                    self.nfo = reg.groups()[0]
                    # r = requests.get(self.nfo)
                    # self.nfo_html = r.text
            else:
                decoup = [y.strip() for y in data.strip().split(':')]
                logging.info('analyse_description : split champs %s', str(decoup))
                if decoup[0] == 'Nom du fichier':
                    self.fichier = decoup[1]
                elif decoup[0] == 'Taille':
                    self.taille = decoup[1]
                elif decoup[0] == 'Catégorie':
                    self.categorie = decoup[1]
                elif len(decoup) == 2:
                    meta[decoup[0]] = decoup[1]
        self.meta = str(meta)
        logging.info('analyse_description : fin')

    def __str__(self):
        return '<%s %s>' % (self.title, self.pubDate)

    class Meta:
        database = db


class ParserArticle(html.parser.HTMLParser):

    def resetin(self):
        self.data = []
        self.tag = None
        self.ondata = False

    def handle_starttag(self, tag, attr):
        if tag == 'item':
            logging.info('ParserArticle.handle_starttag : nouvel item')
            self.data.append(article(link='', description='', pubDate='', comment='',
                                     fichier='', taille='', nfo='', meta=''))
            self.ondata = True
        else:
            self.tag = tag
            logging.info('ParserArticle.handle_starttag : nouveau tag <%s>', tag)

    def handle_endtag(self, tag):
        self.tag = None
        if tag == 'item':
            self.ondata = False
            self.data[-1].analyse_description()

    def handle_data(self, data):
        if self.ondata and (self.tag is not None):
            self.data[-1].__setattr__(self.tag, data)
            logging.info('ParserArticle.handle_data : attribut <%s> <%s>', self.tag, data)


def base_de_donnee(wrap):
    def wrapper():
        db.connect()
        db.create_tables([article], safe=True)
        ret = wrap()
        db.close()
        return ret
    return wrapper


@base_de_donnee
def check_new_article():
    myurl = "http://www.binnews.in/rss/rss_new.php"
    logging.info('check_new_article: debut url <%s>', myurl)
    r = requests.get(myurl)
    logging.info('check_new_article: fin requete status <%d> content-type <%s>',
                 r.status_code, r.headers['content-type'])
    resultat = r.text
    logging.info('check_new_article: taille reponse <%d>', len(resultat))
    parse = ParserArticle()
    parse.resetin()
    parse.feed(resultat)
    logging.info('check_new_article: article detecte <%d>', len(parse.data))
    for x in parse.data:
        try:
            ar = article.get(article.guid == x.guid)
            logging.info('check_new_article: article existant <%s>', ar.guid)
        except article.DoesNotExist:
            x.save()
            logging.info('check_new_article: nouvel article <%s>', x.title)
    logging.info('check_new_article: fin')


@base_de_donnee
def recuperer_tous_articles():
    return [x for x in article.select()]


@base_de_donnee
def recuperer_tous_articles_par_categorie():
    a = [x for x in article.select()]
    a.sort(key=lambda x: x.categorie)
    b = itertools.groupby(a, lambda x: x.categorie)
    c = {x: [z for z in y] for x, y in b}
    return c

# db.connect()
# db.create_tables([article], safe=True)
# print([x for x in article.select()])
# db.close()

# print(recuperer_tous_articles())
check_new_article()
# recuperer_tous_articles_par_categorie()
