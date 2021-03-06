import copy
import html.parser
import logging
import re
from functools import wraps
import click
import requests
from peewee import (
    SqliteDatabase,
    Model,
    CharField,
    IntegerField,
    ForeignKeyField,
    BooleanField,
    DoesNotExist,
    IntegrityError,
    prefetch,
    OperationalError,
)
from minisab.indexeur import MyParserNzbIndex, recherche_indexeur
from . import sabnzbd_util

logger = logging.getLogger("minisab")

db = SqliteDatabase(None)


class Categorie(Model):
    nom = CharField(unique=True)
    categorie_sabnzbd = CharField(default="*")
    autolu = BooleanField(default=False)
    preferee = IntegerField(default=0)

    @classmethod
    def get_favoris(cls):
        return cls.get(cls.nom == "Favoris")

    def __str__(self):
        return "<%s> <%d>" % (self.nom, self.preferee)

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
    categorie = ForeignKeyField(Categorie, related_name="articles")
    categorie_origine = ForeignKeyField(Categorie, related_name="articles_2")
    categorie_str = CharField()
    lu = BooleanField(index=True, default=False)
    annee = IntegerField(default=0)

    def analyse_description(self):
        logger.debug("analyse_description : debut")
        meta = {}
        self.analyse_annee()
        # analyse description
        for x in self.description.split("<br>"):
            data = x.strip()
            logger.debug("analyse_description : champs <%s>", data)
            # detection lien
            if data.startswith("<a href"):
                reg = re.match(r'<a[ ]*href="(.*)">[ ]*Fichier Nfo[ ]*</a>', data)
                logger.debug("analyse_description : lien detecte %s", str(reg))
                if reg is not None:
                    self.nfo = reg.groups()[0]
                    # r = requests.get(self.nfo)
                    # self.nfo_html = r.text
            else:
                decoup = [y.strip() for y in data.strip().split(":")]
                logger.debug("analyse_description : split champs %s", str(decoup))
                if decoup[0] == "Nom du fichier":
                    self.fichier = decoup[1]
                elif decoup[0] == "Taille":
                    self.taille = decoup[1]
                elif decoup[0] == "Catégorie":
                    try:
                        self.categorie_str = decoup[1]
                        self.categorie = Categorie.get(Categorie.nom == decoup[1])
                        self.categorie_origine = Categorie.get(
                            Categorie.nom == decoup[1]
                        )
                    except Categorie.DoesNotExist:
                        self.categorie = Categorie(nom=decoup[1])
                        self.categorie_origine = self.categorie
                        self.categorie.save()
                        logger.info(
                            "Creation nouvelle categorie : %s" % self.categorie.nom
                        )
                elif len(decoup) == 2:
                    meta[decoup[0]] = decoup[1]
        self.meta = str(meta)
        logger.debug("analyse_description : fin")

    def lancer_recherche(self, start_multi=0, stop_multi=9):
        url_nzbindex = "http://www.nzbindex.nl/search/?q={0}&max=100"
        url_binsearch = "https://binsearch.info/?q={0}&max=100"

        liste_fichier = self.fichier.split(" / ")
        cpt_etoile = self.fichier.find("*")
        if cpt_etoile != -1:
            cpt_etoile_fin = self.fichier.find("*", cpt_etoile + 1)
            if cpt_etoile_fin == -1:
                cpt_etoile_fin = cpt_etoile
            for x in range(start_multi, stop_multi + 1, 1):
                liste_fichier.append(
                    self.fichier[0:cpt_etoile]
                    + (("%0" + str(cpt_etoile_fin - cpt_etoile + 1) + "d") % x)
                    + self.fichier[cpt_etoile_fin + 1:]
                )
        # print(liste_fichier)
        for fichier in liste_fichier:
            ret = recherche_indexeur(url_nzbindex, fichier, parseur=MyParserNzbIndex)
            if len(ret) == 0:
                ret = recherche_indexeur(url_binsearch, fichier)
            if len(ret) > 0:
                for item in ret:
                    logger.debug("item %s", str(item))
                    try:
                        rec = Recherche(
                            id_check=item["id"],
                            url=item["url"],
                            taille=item["taille"] if "taille" in item else "Vide",
                            title=item["title"],
                            fichier=fichier,
                            article=self,
                        )
                        rec.save()
                    except IntegrityError:
                        logger.error(
                            "recherche_indexeur : item deja existant <%s>", item["id"]
                        )

    def creer_recherche_tous(self, nom_fichier, url):
        rec = Recherche(
            id_check=0,
            url=url,
            taille="Vide",
            title="Tous",
            fichier=self.fichier,
            article=self,
        )
        rec.save()

    def nettoyer_recherche(self):
        n = Recherche.delete().where(Recherche.article == self).execute()
        logger.debug("%d recherches supprimes pour article %d", n, self.id)

    def analyse_annee(self):
        if self.annee != 0:
            return
        logger.debug("analyse_annee : %s", self.title)
        # analyse annee
        reg = re.match(r".*([0-9]{4}).*", self.title)
        # on essaye en ??/??/????
        if reg is None:
            logger.debug("analyse_annee : premier reg non trouve")
            reg = re.match(r".*[0-9][0-9]/[0-9][0-9]/([0-9]{4}).*", self.title)
        if reg is not None:
            logger.debug("analyse_annee : reg trouve %s", str(reg.group()))
            self.annee = int(reg.groups()[0])
        logger.debug("analyse_annee fin : %d", self.annee)

    def marquer_favoris(self):
        logger.debug("marquer_favorie")
        self.categorie = Categorie.get(Categorie.nom == "Favoris")
        self.save()

    def __str__(self):
        return "<%s %s %s>" % (self.title, self.pubDate, self.lu)

    def printall(self):
        return (
            "<"
            + "<"
            + str(self.title)
            + ">,\n"
            + "<"
            + str(self.link)
            + ">,\n"
            + "<"
            + str(self.description)
            + ">,\n"
            + "<"
            + str(self.pubDate)
            + ">,\n"
            + "<"
            + str(self.comment)
            + ">,\n"
            + "<"
            + str(self.guid)
            + ">,\n"
            + "<"
            + str(self.meta)
            + ">,\n"
            + "<"
            + str(self.nfo)
            + ">,\n"
            + "<"
            + str(self.fichier)
            + ">,\n"
            + "<"
            + str(self.taille)
            + ">,\n"
            + "<"
            + str(self.categorie)
            + ">,\n"
            + "<"
            + str(self.categorie_str)
            + ">,\n"
            + "<"
            + str(self.lu)
            + ">"
            + ">,\n"
            + "<"
            + (str(self.status_nzbd) if "status_nzbd" in dir(self) else "")
            + ">"
        )

    class Meta:
        database = db


class Recherche(Model):
    id_check = IntegerField()
    url = CharField()
    taille = CharField()
    title = CharField()
    id_sabnzbd = CharField(default="")
    fichier = CharField(default="")
    article = ForeignKeyField(Article, related_name="recherche")

    class Meta:
        database = db


class ParserArticle(html.parser.HTMLParser):
    def resetin(self):
        self.data = []
        self.tag = None
        self.ondata = False

    def handle_starttag(self, tag, attr):
        if tag == "item":
            logger.debug("ParserArticle.handle_starttag : nouvel item")
            self.data.append(
                Article(
                    link="",
                    description="",
                    pubDate="",
                    comment="",
                    fichier="",
                    taille="",
                    nfo="",
                    meta="",
                )
            )
            self.ondata = True
        else:
            self.tag = tag
            logger.debug("ParserArticle.handle_starttag : nouveau tag <%s>", tag)

    def handle_endtag(self, tag):
        self.tag = None
        if tag == "item":
            self.ondata = False
            self.data[-1].analyse_description()

    def handle_data(self, data):
        if self.ondata and (self.tag is not None):
            self.data[-1].__setattr__(self.tag, data)
            logger.debug(
                "ParserArticle.handle_data : attribut <%s> <%s>", self.tag, data
            )


def base_de_donnee(wrap):
    @wraps(wrap)
    def wrapper(*args):
        global db
        try:
            db.connect()
            db.create_tables([Article, Recherche, Categorie], safe=True)
            try:
                cat = Categorie.get(Categorie.nom == "Favoris")
            except DoesNotExist:
                cat = Categorie(nom="Favoris", preferee=99)
                cat.save()
            try:
                cat = Categorie.get(Categorie.nom == "Termines")
            except DoesNotExist:
                cat = Categorie(nom="Termines", preferee=98)
                cat.save()
        except OperationalError:
            pass
        ret = wrap(*args)
        db.close()
        return ret

    return wrapper


def check_new_article():
    status = {"resultat": False}
    myurl = "http://www.binnews.in/rss/rss_new.php"
    logger.info("check_new_article: debut url <%s>", myurl)
    r = requests.get(myurl)
    logger.info(
        "check_new_article: fin requete status <%d> content-type <%s>",
        r.status_code,
        r.headers["content-type"],
    )
    resultat = r.text
    logger.debug("check_new_article: taille reponse <%d>", len(resultat))
    parse = ParserArticle(convert_charrefs=True)
    parse.resetin()
    parse.feed(resultat)
    logger.info("check_new_article: article detecte <%d>", len(parse.data))
    nb_nouveau_article = 0
    status["resultat"] = True
    status["nombre_resultat"] = len(parse.data)
    status["nombre_nouveau"] = 0
    for x in parse.data:
        try:
            ar = Article.get(Article.guid == x.guid)
            logger.debug("check_new_article: article existant <%s>", ar.guid)
        except Article.DoesNotExist:
            try:
                x.save()
                status["nombre_nouveau"] += 1
                logger.debug("check_new_article: nouvel article <%s>", x.title)
                nb_nouveau_article = nb_nouveau_article + 1
            except IntegrityError as e:
                logger.error(
                    "Impossible de sauver l"
                    "article : %s %s (%s)" % (x.title, x.guid, str(e))
                )
    logger.info("check_new_article: %d nouveau(x) article(s)", nb_nouveau_article)
    return status


@base_de_donnee
def recuperer_tous_articles():
    return [x for x in Article.select()]


@base_de_donnee
def recuperer_tous_articles_par_categorie(filtres_article=[]):
    logger.debug("recuperer_tous_articles_par_categorie")
    les_articles = (
        Article.select().where(Article.lu == False).order_by(Article.annee.desc())
    )
    les_categories = Categorie.select().order_by(
        Categorie.preferee.desc(), Categorie.nom
    )

    c = [
        (x, x.articles)
        for x in prefetch(les_categories, les_articles)
        if len(x.articles) > 0
    ]

    # filtrage des articles pour detecter certains sur le titre
    logger.debug("nombre filtre %d", len(filtres_article))
    for cat, articles in c:
        cat.avec_filtre = False
        for article in articles:
            article.filtre = False
            for filtre in filtres_article:
                if article.title.find(filtre) != -1:
                    logger.debug("filtre article %s %s", filtre, article.title)
                    article.filtre = True
                    cat.avec_filtre = True

    # si redis est dispo on va inserer les infos sur le statut de telechargement
    status_sab = sabnzbd_util.get_status_sab_redis()
    if len(status_sab) > 0:
        nouvelle_liste_completed = []
        nouvelle_liste_other = []
        liste_id_termine = []
        for z in c:
            if z[0].nom == "Favoris":
                z[0].ids_termine = []
                nouvelle_liste_other = copy.copy(z[1])
                for x in z[1]:
                    x.status_sabnzbd = ""
                    for y in x.recherche:
                        # logger.debug('index, title %s, id sab %s',
                        #              x.title, y.id_sabnzbd)
                        if y.id_sabnzbd in status_sab:
                            x.status_sabnzbd = status_sab[y.id_sabnzbd]
                            logger.debug("index, trouve %s", x.status_sabnzbd)
                    if x.status_sabnzbd != "":
                        nouvelle_liste_other.remove(x)
                        if x.status_sabnzbd == "Completed":
                            nouvelle_liste_completed.insert(0, x)
                            liste_id_termine.append(x.id)
                        else:
                            nouvelle_liste_other.insert(0, x)
        if (
            (len(nouvelle_liste_completed) > 0) or (len(nouvelle_liste_other) > 0)
        ) and (c[0][0].nom == "Favoris"):
            c[0] = (c[0][0], nouvelle_liste_completed + nouvelle_liste_other)
            c[0][0].ids_termine = liste_id_termine

    return c


@base_de_donnee
def recuperer_tous_articles_pour_une_categorie(nom_categorie, lu=False):
    c = []
    try:
        cat = Categorie.get(Categorie.nom == nom_categorie)
        c = [
            x
            for x in Article.select().where(
                (Article.lu == lu) & (Article.categorie == cat)
            )
        ]
        logger.debug("recuperer_tous_articles_pour_une_categorie cat %s", nom_categorie)
        for x in c:
            logger.debug(
                "lu %d cat or %s title %s", x.lu, x.categorie_origine.nom, x.title
            )
    except DoesNotExist as e:
        logger.error("nom categorie inconnue : %s(%s)", nom_categorie, str(e))

    return c


@base_de_donnee
def recuperer_tous_articles_pour_une_categorie_lu(
    nom_categorie, numero_bloc=0, nombre_decoupage=100
):
    c = []
    try:
        cat = Categorie.get(Categorie.nom == nom_categorie)
        logger.debug(str(cat))
        c = [x for x in Article.select().where(Article.categorie_origine == cat)]
        nb_bloc = int(len(c) / nombre_decoupage) + 1
        res = c[numero_bloc * nombre_decoupage: (numero_bloc + 1) * nombre_decoupage]
        logger.debug("nombre de bloc : %d" % nb_bloc)
        logger.debug("nombre d element : %d" % len(c))
    except DoesNotExist as e:
        logger.error("nom categorie inconnue : %s(%s)", nom_categorie, str(e))

    return res, nb_bloc


@click.group()
def cli():
    pass


@cli.command("check_sab")
def cmd_check_sabnzbd():
    sabnzbd_util.check_sabnzbd()


@cli.command()
@base_de_donnee
def patch_annee():
    for x in Article.select():
        x.analyse_annee()
        x.save()


@cli.command("check")
@base_de_donnee
def cmd_check_new_article():
    check_new_article()


if __name__ == "__main__":
    # config.config_file = './config.json'
    # a = config(init_from_env=False)
    # import logging.config
    from settings import log_config

    logging.config.dictConfig(log_config)
    cli()
