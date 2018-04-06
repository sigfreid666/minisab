from flask import Flask, render_template, abort, Blueprint, request, jsonify
# from ownmodule import sabnzbd, sabnzbd_nc_cle_api
import requests
import logging
import logging.config
import itertools
import newminisab
import redis
from settings import host_redis, port_redis, host_sabG, sabnzbd_nc_cle_api
from settings import log_config, port_sabG

filtre_article = [ '*** MOT DE PASSE ***' ]

logging.config.dictConfig(log_config)
# logger.setLevel(logging.DEBUG)

version = '2.9b'
bp = Blueprint('minisab', __name__, static_folder='/minisab/static')
app = Flask(__name__)
logger = app.logger # logging.getLogger('gunicorn.glogging.Logger')
gunicorn_logger = logging.getLogger('gunicorn.error')
app.logger.handlers = gunicorn_logger.handlers


nom_cat_sab = 'minisab_categorie_sabnzbd'


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
                           categorie_sabnzbd=get_categorie_sabnzbd(),
                           version=version,
                           categorie_favoris_id=newminisab.Categorie.get_favoris().id)


@bp.route('/maj')
def mise_a_jour():
    logger.info('Requete : /maj')
    return jsonify(newminisab.check_new_article())


@bp.route('/check_sab')
def check_sab():
    logger.info('Requete : /maj')
    return jsonify(newminisab.check_sabnzbd())


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
        cat_sab = get_categorie_sabnzbd()
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
                               categorie_sabnzbd=get_categorie_sabnzbd(),
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
                        delete_history_sab(y.id_sabnzbd)
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
        return render_template('./article.html', item=ar,
                               categorie_sabnzbd=get_categorie_sabnzbd(),
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
        rec.id_sabnzbd = telechargement_sabnzbd(rec.article.title,
                                                rec.url, categorie)
        rec.save()
        if host_redis is not None:
            red = None
            try:
                red = redis.StrictRedis(host=host_redis, port=port_redis)
                red.rpush('sabdownload', rec.id_sabnzbd)
                red.rpush('sabdownload', rec.article.id)
            except redis.exceptions.ConnectionError as e:
                logging.error('Impossible de se connecter à Redis : %s', str(e))
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
                           categorie_sabnzbd=get_categorie_sabnzbd())


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


def get_categorie_sabnzbd():
    categorie_sabnzbd = []
    if host_redis is not None:
        red = None
        try:
            red = redis.StrictRedis(host=host_redis, port=port_redis)
            categorie_sabnzbd = [x.decode('utf-8')
                                 for x in
                                 red.lrange(nom_cat_sab, 0, -1)]
        except redis.exceptions.ConnectionError as e:
            logging.error('Impossible de se connecter à Redis : %s', str(e))
    if (len(categorie_sabnzbd) == 0) and (host_sabG is not None):
        param = {'apikey': sabnzbd_nc_cle_api,
                 'output': 'json',
                 'mode': 'get_cats'}
        myurl = "http://{0}:{1}/sabnzbd/api".format(
                host_sabG,
                port_sabG)
        r = requests.get(myurl, params=param)
        resultat = r.json()
        if 'categories' in resultat:
            if (host_redis is not None) and\
               (red is not None):
                red.lpush(nom_cat_sab, *[x.encode('ascii')
                                         for x in resultat['categories']])
                red.expire(nom_cat_sab, 600)
            return resultat['categories']
        else:
            return ''
    else:
        return categorie_sabnzbd


def telechargement_sabnzbd(title, url, categorie):
    if host_sabG is not None:
        param = {'apikey': sabnzbd_nc_cle_api,
                 'output': 'json',
                 'mode': 'addurl',
                 'name': url,
                 'nzbname': title,
                 'cat': categorie}
        myurl = "http://{0}:{1}/sabnzbd/api".format(
                host_sabG,
                port_sabG)
        r = requests.get(myurl, params=param)
        resultat = r.json()
        if resultat['status']:
            return resultat['nzo_ids'][0]
        else:
            return ''
    else:
        return ''


def status_sabnzbd():
    if host_sabG is not None:
        param = {'apikey': sabnzbd_nc_cle_api,
                 'output': 'json',
                 'limit': '100',
                 'mode': 'history'}
        myurl = "http://{0}:{1}/sabnzbd/api".format(
                host_sabG,
                port_sabG)
        try:
            r = requests.get(myurl, params=param)
            resultat = r.json()
            param = {'apikey': sabnzbd_nc_cle_api,
                     'output': 'json',
                     'mode': 'queue'}
            myurl = "http://{0}:{1}/sabnzbd/api".format(
                    host_sabG,
                    port_sabG)
            r = requests.get(myurl, params=param)
            resultat2 = r.json()
            resultat_total = itertools.chain(resultat['history']['slots'],
                                             resultat2['queue']['slots'])
            return {x['nzo_id']: x['status'] for x in resultat_total}
        except requests.exceptions.ConnectionError:
            return {}
    else:
        return {}


def delete_history_sab(id_sab):
    if host_sabG is not None:
        param = {'apikey': sabnzbd_nc_cle_api,
                 'output': 'json',
                 'name': 'delete',
                 'value': id_sab,
                 'mode': 'history'}
        myurl = "http://{0}:{1}/sabnzbd/api".format(
                host_sabG,
                port_sabG)
        r = requests.get(myurl, params=param)
        return r.status_code
    else:
        return 0


app.register_blueprint(bp, url_prefix='/minisab')

if __name__ == "__main__":
    # app.run(host="0.0.0.0", port=9030)
    app.run(host="0.0.0.0", port=5000)
