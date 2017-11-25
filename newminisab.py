import requests
from peewee import *
import html.parser
import re
import logging
from indexeur import recherche_indexeur, MyParserNzbIndex
import click
from settings import dbfile, host_sabG, sabnzbd_nc_cle_api, host_redis, port_redis
from functools import wraps
import redis
import itertools

# if __name__ == "__main__":
#     import logging.config
#     from settings import log_config
#     print(log_config)
#     logging.config.dictConfig(log_config)

logger = logging.getLogger(__name__)

db = SqliteDatabase(dbfile)


class Categorie(Model):
    nom = CharField(unique=True)
    categorie_sabnzbd = CharField(default='*')
    autolu = BooleanField(default=False)
    preferee = IntegerField(default=0)

    def get_favoris():
        return Categorie.get(Categorie.nom == 'Favoris')

    def __str__(self):
        return '<%s> <%d>' % (self.nom, self.preferee)

    class Meta:
        database = db


class Article(Model):
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
    categorie = ForeignKeyField(Categorie, related_name='articles')
    categorie_origine = ForeignKeyField(Categorie, related_name='articles_2')
    categorie_str = CharField()
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
                        self.categorie_str = decoup[1]
                        self.categorie = Categorie.get(Categorie.nom == decoup[1])
                        self.categorie_origine = Categorie.get(Categorie.nom == decoup[1])
                    except Categorie.DoesNotExist:
                        self.categorie = Categorie(nom=decoup[1])
                        self.categorie.save()
                        logger.info('Creation nouvelle categorie : %s' % self.categorie.nom)
                elif len(decoup) == 2:
                    meta[decoup[0]] = decoup[1]
        self.meta = str(meta)
        logger.debug('analyse_description : fin')

    def lancer_recherche(self, start_multi=0, stop_multi=9):
        url_nzbindex = 'http://www.nzbindex.nl/search/?q={0}&max=100'
        url_binsearch = 'https://binsearch.info/?q={0}&max=100'

        liste_fichier = self.fichier.split(' / ')
        cpt_etoile = self.fichier.find('*')
        if cpt_etoile != -1:
            cpt_etoile_fin = self.fichier.find('*', cpt_etoile + 1)
            if cpt_etoile_fin == -1:
                cpt_etoile_fin = cpt_etoile
            for x in range(start_multi, stop_multi + 1, 1):
                liste_fichier.append(self.fichier[0:cpt_etoile] +
                                     (('%0' + str(cpt_etoile_fin - cpt_etoile + 1) + 'd') % x) +
                                     self.fichier[cpt_etoile_fin + 1:])
        # print(liste_fichier)
        for fichier in liste_fichier:
            ret = recherche_indexeur(url_nzbindex, fichier, parseur=MyParserNzbIndex)
            if len(ret) == 0:
                ret = recherche_indexeur(url_binsearch, fichier)
            if len(ret) > 0:
                for item in ret:
                    logger.info('item %s', str(item))
                    try:
                        rec = Recherche(id_check=item['id'],
                                        url=item['url'],
                                        taille=item['taille'] if 'taille' in item else 'Vide',
                                        title=item['title'],
                                        fichier=fichier,
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

    def marquer_favoris(self):
        logger.debug('marquer_favorie')
        self.categorie = Categorie.get(Categorie.nom == 'Favoris')
        self.save()

    def liste_categorie():
        a = (Article.select(Article.categorie, fn.Count(Article.categorie).alias('nb'))
                    .where(Article.lu == False)
                    .group_by(Article.categorie))
        return [(x.categorie, x.nb) for x in a]

    def __str__(self):
        return '<%s %s %s>' % (self.title, self.pubDate, self.lu)

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
                '<' + str(self.categorie_str) + '>,\n' +
                '<' + str(self.lu) + '>' + '>,\n' +
                '<' + (str(self.status_nzbd) if 'status_nzbd' in dir(self) else '') + '>')

    class Meta:
        database = db


class Recherche(Model):
    id_check = IntegerField(unique=True)
    url = CharField()
    taille = CharField()
    title = CharField()
    id_sabnzbd = CharField(default='')
    fichier = CharField(default='')
    article = ForeignKeyField(Article, related_name='recherche')

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
            self.data.append(Article(link='', description='', pubDate='', comment='',
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
    def wrapper(*args):
        global db
        try:
            db.connect()
            db.create_tables([Article, Recherche, Categorie], safe=True)
            try:
                cat = Categorie.get(Categorie.nom == 'Favoris')
            except DoesNotExist:
                cat = Categorie(nom="Favoris", preferee=99)
                cat.save()
        except OperationalError:
            pass
        ret = wrap(*args)
        db.close()
        return ret
    return wrapper


@click.group()
def cli():
    pass

def status_sabnzbd():
    if host_sabG is not None:
        param = {'apikey': sabnzbd_nc_cle_api,
                 'output': 'json',
                 'limit': '100',
                 'mode': 'history'}
        myurl = "http://{0}:{1}/sabnzbd/api".format(
                host_sabG,
                9000)
        try:
            r = requests.get(myurl, params=param)
            resultat = r.json()
            param = {'apikey': sabnzbd_nc_cle_api,
                     'output': 'json',
                     'mode': 'queue'}
            myurl = "http://{0}:{1}/sabnzbd/api".format(
                    host_sabG,
                    9000)
            r = requests.get(myurl, params=param)
            resultat2 = r.json()
            resultat_total = itertools.chain(resultat['history']['slots'],
                                             resultat2['queue']['slots'])
            return [ (x['nzo_id'], x['status']) for x in resultat_total ]
        except requests.exceptions.ConnectionError:
            return {}
    else:
        return {}

@cli.command('check_sab')
def check_sabnzbd():
    status_possible = ('Completed', 'Failed', 'Downloading')
    if host_redis is not None:
        red = None
        try:
            red = redis.StrictRedis(host=host_redis, port=port_redis)
            st_sb = status_sabnzbd()
            # st_sb = [('aaaaaa', 'Completed'), ('bbbbbb', 'Failed'), ('ccccccc', 'Downloading'), ('ddddddd', 'Downloading'), ('eeeeeee', 'Failed'), ('ffffffff', 'Completed')]
            if len(st_sb) > 0: # on pete tous
                for status in status_possible:
                    red.srem('sab_' + status, *red.smembers('sab_' + status))
            for idsab, status in st_sb:
                if status in status_possible:
                    red.sadd('sab_' + status, idsab)
            for status in status_possible:
                print('status :', status, 'members :', red.smembers('sab_' + status))
        except redis.exceptions.ConnectionError as e:
            logging.error('Impossible de se connecter à Redis : %s', str(e))

@cli.command('test')
@base_de_donnee
def test():
    a = Article.select(Article.categorie, fn.Count(Article.categorie).alias('nb')).where(Article.lu == False).group_by(Article.categorie)
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
    parse = ParserArticle(convert_charrefs=True)
    parse.resetin()
    parse.feed(resultat)
    logger.info('check_new_article: article detecte <%d>', len(parse.data))
    nb_nouveau_article = 0
    for x in parse.data:
        try:
            ar = Article.get(Article.guid == x.guid)
            logger.debug('check_new_article: article existant <%s>', ar.guid)
        except Article.DoesNotExist:
            try:
                x.save()
                logger.debug('check_new_article: nouvel article <%s>', x.title)
                nb_nouveau_article = nb_nouveau_article + 1
            except IntegrityError as e:
                logger.error('Impossible de sauver l''article : %s %s (%s)' % (x.title, x.guid, str(e)))
    logger.info('check_new_article: %d nouveau(x) article(s)', nb_nouveau_article)


@base_de_donnee
def recuperer_tous_articles():
    return [x for x in Article.select()]

@cli.command('test')
def test():
    recuperer_tous_articles_par_categorie()


@base_de_donnee
def recuperer_tous_articles_par_categorie():
    logger.debug('recuperer_tous_articles_par_categorie')
    # favoris = [x for x in article.select()
    #                              .where(article.lu == False)
    #                              .join(categorie)
    #                              .where(categorie.nom == 'Favoris')]
    c = [(x, x.articles) for x in Categorie.select(Categorie, Article)
                                           .join(Article)
                                           .where(Article.lu == False)
                                           .order_by(Categorie.preferee.desc(),
                                                     Categorie.nom,
                                                     Article.annee.desc())
                                           .aggregate_rows()]
    # print([(x.nom, len(c[x])) for x in c])
    return c


@base_de_donnee
def recuperer_tous_articles_pour_une_categorie(nom_categorie):
    c = []
    try:
        cat = Categorie.get(Categorie.nom == nom_categorie)
        c = [x for x in Article.select()
                               .where((Article.lu == False) &
                                      (Article.categorie == cat))]
    except DoesNotExist as e:
        logger.error('nom categorie inconnue : %s(%s)', nom_categorie, str(e))

    return c


@cli.command()
@base_de_donnee
def patch_annee():
    for x in Article.select():
        x.analyse_annee()
        x.save()


if __name__ == "__main__":
    import logging.config
    from settings import log_config
    logging.config.dictConfig(log_config)
    cli()
