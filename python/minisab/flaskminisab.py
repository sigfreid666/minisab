from flask import Flask, render_template, abort, Blueprint, request, jsonify, url_for, current_app, redirect
# from ownmodule import sabnzbd, sabnzbd_nc_cle_api
import requests
import logging
import logging.config
import itertools
from . import newminisab
import redis
from . import sabnzbd_util
from . import settings
from . import __version__
# import util

filtre_article = [ '*** MOT DE PASSE ***' ]

# logging.config.dictConfig(log_config)
# logger.setLevel(logging.DEBUG)
logger = logging.getLogger('minisab')

version = '2.11'

nom_cat_sab = 'minisab_categorie_sabnzbd'

bp = Blueprint('minisab', __name__, static_folder='/minisab/static')

def render_template_categorie(id_categorie):
    cat = newminisab.Categorie.get(newminisab.Categorie.id == id_categorie)
    if cat is not None:
        items = (newminisab.recuperer_tous_articles_pour_une_categorie(
                 cat.nom))
        return (render_template('./categorie.html',
                                categorie=cat,
                                items=items),
                render_template('./categorie_end.html',
                                categorie=cat,
                                items=items))
    else:
        return ''


@bp.route("/")
def index():
    logger.info('Requete /')
    articles = newminisab.recuperer_tous_articles_par_categorie(filtre_article)
    logger.debug('index, articles %d', len(articles))
    for cat, x in articles:
        logger.debug('cat %s nb items %d', cat.nom, len(x))
    return render_template('./minifluxlist.html', titlepage='Miniflux',
                           articles=articles,
                           categorie_sabnzbd=sabnzbd_util.get_categorie_sabnzbd(),
                           version=__version__,
                           categorie_favoris_id=newminisab.Categorie.get_favoris().id)


@bp.route('/maj')
def mise_a_jour():
    logger.info('Requete : /maj')
    return jsonify(newminisab.check_new_article())


@bp.route('/check_sab')
def check_sab():
    logger.info('Requete : /maj')
    return jsonify(sabnzbd_util.check_sabnzbd())


@bp.route('/check_urls')
def check_urls():
    logger.info('Requete : /check_urls')
    resultat = sabnzbd_util.merge_nzb()
    for termine_id, termine_fichier in resultat['article_termine']:
        ar = newminisab.Article.get(newminisab.Article.id == termine_id)
        url = (current_app.config['MINISABINV_URL_EXTERNE'] +
               url_for('minisab.get_nzb',
                       id_article=termine_id))
        logger.debug('ajout recherche tous pour %s et %s',
                     termine_fichier, url)
        ar.creer_recherche_tous(termine_fichier, url)
    return jsonify(resultat)


@bp.route('/nzb/<int:id_article>')
def get_nzb(id_article=None):
    logger.debug('get_nzb %d', id_article)
    try:
        with open(settings.filename_dump(id_article), mode='r') as fichier:
            content = fichier.read()
        return content
    except FileNotFoundError:
        abort(404)

@bp.route('/nettoyage_traitement/<int:id_article>')
def nettoyage_traitement(id_article):
    logger.debug('nettoyage_traitement %d', id_article)
    sabnzbd_util.nettoyage_traitement(id_article)
    return "OK"


@bp.route('/affiche_urls')
def affiche_urls():
    logger.info('Affichage des urls')
    num_art, table_urls = sabnzbd_util.get_info_affiche_urls()
    return render_template('./traitement_en_cours.html',
                           version=version,
                           numeros_articles=num_art,
                           table_urls=table_urls)


@bp.route('/article/<int:id_article>/favoris/categorie')
def marquer_article_favoris_categorie(id_article=None):
    logger.info('Requete %s', request.url)
    try:
        ar = newminisab.Article.get(newminisab.Article.id == id_article)
        id_cat_ar = ar.categorie.id
        ar.marquer_favoris()
        ar.lancer_recherche()
        logger.info('marquer favoris %d nb recherche %d',
                    id_article, len(ar.recherche))
        ar.save()

        cat_fav = newminisab.Categorie.get_favoris()
        logger.debug('cat favoris %d %s', cat_fav.id, cat_fav.nom)
        cat_sab = sabnzbd_util.get_categorie_sabnzbd()
        fav_html = render_template_categorie(cat_fav.id)
        sab_html = render_template_categorie(id_cat_ar)
        article_html = render_template('./article.html', item=ar,
                                       categorie=ar.categorie,
                                       categorie_sabnzbd=cat_sab,
                                       categorie_favoris_id=cat_fav.id)
        articles = newminisab.recuperer_tous_articles_par_categorie()
        temp_barre = render_template('./barre_categorie.html', articles=articles)

        return jsonify((article_html, *fav_html, *sab_html, temp_barre))
    except newminisab.Article.DoesNotExist:
        abort(404)


@bp.route('/article/<int:id_article>/favoris')
def marquer_article_favoris(id_article=None):
    logger.info('Requete %s', request.url)
    try:
        ar = newminisab.Article.get(newminisab.Article.id == id_article)
        ar.marquer_favoris()
        logger.info('marquer favoris %d',
                    id_article)
        ar.save()
        return render_template('./article.html', item=ar,
                               categorie=ar.categorie,
                               categorie_sabnzbd=sabnzbd_util.get_categorie_sabnzbd(),
                               categorie_favoris_id=newminisab.Categorie.get_favoris().id)
    except newminisab.Article.DoesNotExist:
        abort(404)


@bp.route('/articles/lu/<int:lunonlu>', methods=['GET', 'POST'])
def marquer_article_lu(lunonlu=0):
    logger.info('Requete /article/lu %s', request.method)
    try:
        cat_id = None
        if request.method == 'POST':
            data_json = request.get_json()
            for art_id in data_json:
                ar = newminisab.Article.get(newminisab.Article.id == art_id)
                cat_id = ar.categorie_origine.id
                ar.lu = True if lunonlu == 0 else False
                for y in ar.recherche:
                    logger.info('article_lu, title %s, id sab %s',
                                ar.title, y.id_sabnzbd)
                    if y.id_sabnzbd != '':
                        sabnzbd_util.delete_history_sab(y.id_sabnzbd)
                        y.id_sabnzbd = ''
                        y.save()
                ar.categorie = ar.categorie_origine
                ar.save()
        html_categorie = render_template_categorie(cat_id)
        return jsonify(*html_categorie)
    except newminisab.Article.DoesNotExist:
        abort(404)


@bp.route('/article/<id_article>/recherche/<int:stop_multi>')
@bp.route('/article/<id_article>/recherche',
          defaults={'stop_multi': 0})
def recherche_article(id_article, stop_multi):
    logger.info('Requete %s', request.url)
    try:
        # print('lancer recherche %s %d' % (id_article, stop_multi))
        ar = newminisab.Article.get(newminisab.Article.id == id_article)
        ar.lancer_recherche(start_multi=1, stop_multi=stop_multi)
        ar = newminisab.Article.get(newminisab.Article.id == id_article)
        return render_template('./article.html', item=ar,
                               categorie=ar.categorie,
                               categorie_sabnzbd=sabnzbd_util.get_categorie_sabnzbd(),
                               categorie_favoris_id=newminisab.Categorie.get_favoris().id)
    except newminisab.Article.DoesNotExist:
        abort(404)


@bp.route('/article/<id_article>/nettoyer_recherche')
def nettoyer_recherche(id_article):
    try:
        ar = newminisab.Article.get(newminisab.Article.id == id_article)
        ar.nettoyer_recherche()
        ar = newminisab.Article.get(newminisab.Article.id == id_article)
        return render_template('./article.html', item=ar,
                               categorie=ar.categorie,
                               categorie_sabnzbd=sabnzbd_util.get_categorie_sabnzbd(),
                               categorie_favoris_id=newminisab.Categorie.get_favoris().id)
    except newminisab.Article.DoesNotExist:
        abort(404)


@bp.route('/recherche/<id_recherche>/telecharger/<categorie>')
@bp.route('/recherche/<id_recherche>/telecharger/',
          defaults={'categorie': '*'})
def lancer_telecharger(id_recherche, categorie):
    logger.info('Requete %s', request.url)
    try:
        rec = newminisab.Recherche.get(newminisab.Recherche.id == id_recherche)
        res_tele = sabnzbd_util.telechargement_sabnzbd(rec.article.title,
                                                rec.url, categorie)
        if 'nzo_ids' in res_tele:
            rec.id_sabnzbd = res_tele['nzo_ids']
            rec.save()
            sabnzbd_util.redis_sav_recherche(rec)
        return 'OK'
    except newminisab.Article.DoesNotExist:
        abort(404)


@bp.route('/article/<int:id_article>/tout_telecharger/<categorie>')
@bp.route('/article/<int:id_article>/tout_telecharger/',
          defaults={'categorie': '*'})
def lancer_tout_telecharger(id_article, categorie):
    logger.info('Requete %s', request.url)
    try:
        rec = (newminisab.Recherche.select()
                                   .where(newminisab.Recherche.article == id_article))
        urls = [r.url for r in rec]
        logger.debug('Nombre url trouve %d', len(urls))
        logger.debug('recherche trouve %s', str(urls))
        sabnzbd_util.save_urls(id_article, urls)
        return 'OK'
    except newminisab.Article.DoesNotExist:
        abort(404)


@bp.route('/categorie/<int:id_categorie>')
@bp.route('/categorie/<int:id_categorie>/<int:id_categorie2>')
def get_categorie(id_categorie=None, id_categorie2=None):
    logger.info('Requete %s', request.url)
    template = []
    for id_cat in (id_categorie, id_categorie2):
        if id_cat is None:
            continue
        cat = newminisab.Categorie.get(newminisab.Categorie.id == id_cat)
        if cat is not None:
            logger.debug('Categorie nom : %s', cat.nom)
            items = (newminisab.recuperer_tous_articles_pour_une_categorie(
                     cat.nom))
            logger.debug('Categorie nombre element : %s', len(items))
            for x in items:
                logger.debug('Cat : %s', x.categorie_origine.nom)
            template.append(render_template('./categorie.html',
                                            categorie=cat,
                                            items=items))
            template.append(render_template('./categorie_end.html',
                                            categorie=cat,
                                            items=items))
        return jsonify(template)
    else:
        abort(404)


@bp.route('/categorie/historique/<int:id_categorie>/<int:taille_bloc>/<int:num_bloc>')
def categorie_historique(id_categorie=None, taille_bloc=100, num_bloc=0):
    logger.info('Requete %s %d', request.url, id_categorie)
    obj_categorie = newminisab.Categorie.get(newminisab.Categorie.id == id_categorie)
    articles, nb_bloc = newminisab.recuperer_tous_articles_pour_une_categorie_lu(obj_categorie.nom, num_bloc, taille_bloc)

    return render_template('./minifluxlistcomplete.html',
                           categorie=obj_categorie,
                           articles=articles,
                           taille_bloc=taille_bloc,
                           num_bloc=num_bloc,
                           nb_bloc=nb_bloc)


@bp.route('/categories')
def categorie_liste():
    logger.info('Requete %s', request.url)
    articles = newminisab.recuperer_tous_articles_par_categorie()
    logger.debug('nb articles %d', len(articles))
    return render_template('./barre_categorie.html', articles=articles)


@bp.route('/categories/index/')
def categories_index():
    return render_template('./categories_index.html',
                           categories=[x for x in newminisab.Categorie.select()],
                           categorie_sabnzbd=sabnzbd_util.get_categorie_sabnzbd())


@bp.route('/categorie/<int:id_categorie>/sabnzbd/<cat_sab>')
def change_sab_categorie(id_categorie=None, cat_sab=None):
    cat = newminisab.Categorie.get(newminisab.Categorie.id == id_categorie)
    cat.categorie_sabnzbd = cat_sab
    cat.save()
    return 'OK'


@bp.route('/categorie/<int:id_categorie>/preferee/<int:preferee>')
def change_sab_preferee(id_categorie=None, preferee=0):
    cat = newminisab.Categorie.get(newminisab.Categorie.id == id_categorie)
    cat.preferee = preferee
    cat.save()
    return 'OK'


@bp.route('/config', methods=['GET', 'POST'])
def flaskconfig():
    logger.debug('flaskconfig : method : %s', request.method)
    if request.method == 'POST':
        data_json = request.form
        # logger.debug('data : %s', request.get_data())
        logger.debug('content length : %s', request.content_length)
        logger.debug('change config : %s', str([data_json[x] for x in data_json.keys()]))
        a = settings.ConfigBase(current_app).maj_config(data_json)
        logger.debug('New config : %s', str(a))

        current_app.config.from_object(a)
        if newminisab.db.is_closed():
            newminisab.db.close()
        newminisab.db.init(current_app.config['MINISAB_AUTRE_DBFILE'])
        logger.info('mise a jour configuration')
        logger.info('chargement configuration : %s', settings.ConfigBase.strConfig(current_app.config))

    config_app = settings.ConfigBase.get_config(current_app)
    return render_template('./config.html',
                           config=config_app)


