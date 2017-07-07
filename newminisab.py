import requests
from peewee import *
import html.parser
import re
import logging
import itertools
from indexeur import recherche_indexeur, MyParserNzbIndex
import click
from settings import dbfile, logfile
from functools import wraps

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# create a file handler
handler = logging.FileHandler(logfile, encoding='utf-8')
handler.setLevel(logging.DEBUG)

# create stderr handler
handlerstd = logging.StreamHandler()
handlerstd.setLevel(logging.DEBUG)

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


class categorie(Model):
    nom = CharField(unique=True)
    categorie_sabnzbd = CharField(default='*')
    autolu = BooleanField(default=False)
    preferee = IntegerField(default=0)

    class Meta:
        database = db


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
    categorie = ForeignKeyField(categorie, related_name='articles')
    favorie = BooleanField(index=True, default=False)
    lu = BooleanField(index=True, default=False)
    annee = IntegerField(default=0)

    def analyse_description(self):
        logger.debug('analyse_description : debut')
        meta = {}
        self.analyse_annee()
        # analyse description
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
                    try:
                        self.categorie = categorie.get(categorie.nom == decoup[1])
                    except categorie.DoesNotExist:
                        self.categorie = categorie(nom=self.categorie)
                        self.categorie.save()
                elif len(decoup) == 2:
                    meta[decoup[0]] = decoup[1]
        self.meta = str(meta)
        logger.debug('analyse_description : fin')

    def lancer_recherche(self):
        url_nzbindex = 'http://www.nzbindex.nl/search/?q={0}&max=100'
        url_binsearch = 'https://binsearch.info/?q={0}&max=100'

        self.calculer_categorie_favoris()

        ret = recherche_indexeur(url_nzbindex, self.fichier, parseur=MyParserNzbIndex)
        if len(ret) == 0:
            ret = recherche_indexeur(url_binsearch, self.fichier)
        if len(ret) > 0:
            self.calculer_categorie_favoris()
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

    def analyse_annee(self):
        if self.annee != 0:
            return
        logger.debug('analyse_annee : %s', self.title)
        # analyse annee
        reg = re.match(r'.*([0-9]{4}).*', self.title)
        # on essaye en ??/??/????
        if reg is None:
            logger.debug('analyse_annee : premier reg non trouve')
            reg = re.match(r'.*[0-9][0-9]/[0-9][0-9]/([0-9]{4}).*', self.title)
        if reg is not None:
            logger.debug('analyse_annee : reg trouve %s', str(reg.group()))
            self.annee = int(reg.groups()[0])
        logger.debug('analyse_annee fin : %d', self.annee)

    def liste_categorie():
        a = (article.select(article.categorie, fn.Count(article.categorie).alias('nb'))
                    .where(article.lu == False)
                    .group_by(article.categorie))
        return [(x.categorie, x.nb) for x in a]

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
                '<' + str(self.lu) + '>' + '>,\n' +
                '<' + (str(self.status_nzbd) if 'status_nzbd' in dir(self) else '') + '>')

    class Meta:
        database = db


class recherche(Model):
    id_check = IntegerField(unique=True)
    url = CharField()
    taille = CharField()
    title = CharField()
    id_sabnzbd = CharField(default='')
    fichier = CharField(default='')
    article = ForeignKeyField(article, related_name='recherche')

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


@cli.command('test')
@base_de_donnee
def test():
    a = article.select(article.categorie, fn.Count(article.categorie).alias('nb')).where(article.lu == False).group_by(article.categorie)
    print([(x.categorie, x.nb) for x in a])

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
    favoris = [x for x in article.select()
                                 .where((article.favorie == True) &
                                        (article.lu == False))]
    a = [x for x in article.select().where((article.favorie == False) &
                                           (article.lu == False))]
    # a.sort(key=lambda x: (x.categorie, 3000 - x.annee))
    # b = itertools.groupby(a, lambda x: x.categorie)
    a = categorie.select()[0]
    print(type(a))
    print(dir(a))
    c = {x: x.articles for x in categorie.select()}
    return (c, favoris)


@cli.command()
@base_de_donnee
def patch_annee():
    for x in article.select():
        x.analyse_annee()
        x.save()


if __name__ == "__main__":
    cli()
