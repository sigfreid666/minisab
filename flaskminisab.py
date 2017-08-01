from flask import Flask, render_template, abort, Blueprint, request
import newminisab
# from ownmodule import sabnzbd, sabnzbd_nc_cle_api
import requests
import logging
import itertools
import redis
from settings import host_redis, port_redis, host_sabG, sabnzbd_nc_cle_api

logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)

version = '2.5a'
bp = Blueprint('minisab', __name__, static_url_path='/minisab/static',
               static_folder='static')

nom_cat_sab = 'minisab_categorie_sabnzbd'


@bp.route("/")
def index():
    articles = newminisab.recuperer_tous_articles_par_categorie()
    logger.debug('index, articles %d', len(articles))
    status_sab = status_sabnzbd()
    logger.debug('index, statut sab %s', str(status_sab))
    for z in articles:
        if z[0].nom == 'Favoris':
            for x in z[1]:
                for y in x.recherche:
                    logger.debug('index, title %s, id sab %s',
                                            x.title, y.id_sabnzbd)
                    if y.id_sabnzbd in status_sab:
                        x.status_sabnzbd = status_sab[y.id_sabnzbd]
                        logger.debug('index, trouve %s', x.status_sabnzbd)
    # articles = ([(x[0], x[1]) for x in articles.items()])
    return render_template('./minifluxlist.html', titlepage='Miniflux',
                           articles=articles,
                           categorie_sabnzbd=get_categorie_sabnzbd(),
                           version=version,
                           categorie_favoris_id=newminisab.categorie.get_favoris().id)


@bp.route('/article/<int:id_article>/favoris')
def marquer_article_favoris(id_article=None):
    try:
        ar = newminisab.article.get(newminisab.article.id == id_article)
        ar.marquer_favoris()
        ar.lancer_recherche()
        logger.info('marquer favoris %d nb recherche %d',
                               id_article, len(ar.recherche))
        ar.save()
        return render_template('./article.html', item=ar,
                               categorie=ar.categorie,
                               categorie_sabnzbd=get_categorie_sabnzbd(),
                               categorie_favoris_id=newminisab.categorie.get_favoris().id)
    except newminisab.article.DoesNotExist:
        abort(404)


@bp.route('/articles/lu', methods=['GET', 'POST'])
def marquer_article_lu():
    try:
        if request.method == 'POST':
            data_json = request.get_json()
            for art_id in data_json:
                ar = newminisab.article.get(newminisab.article.id == art_id)
                ar.lu = True
                for y in ar.recherche:
                    logger.info('article_lu, title %s, id sab %s',
                                           ar.title, y.id_sabnzbd)
                    if y.id_sabnzbd != '':
                        delete_history_sab(y.id_sabnzbd)
                ar.save()
        return "OK"
    except newminisab.article.DoesNotExist:
        abort(404)


@bp.route('/article/<id_article>/recherche/<int:stop_multi>')
@bp.route('/article/<id_article>/recherche',
          defaults={'stop_multi': 0})
def recherche_article(id_article, stop_multi):
    try:
        # print('lancer recherche %s %d' % (id_article, stop_multi))
        ar = newminisab.article.get(newminisab.article.id == id_article)
        ar.lancer_recherche(start_multi=1, stop_multi=stop_multi)
        return render_template('./article.html', item=ar,
                               categorie_sabnzbd=get_categorie_sabnzbd(),
                               categorie_favoris_id=newminisab.categorie.get_favoris().id)
    except newminisab.article.DoesNotExist:
        abort(404)


@bp.route('/recherche/<id_recherche>/telecharger/<categorie>')
@bp.route('/recherche/<id_recherche>/telecharger/',
          defaults={'categorie': '*'})
def lancer_telecharger(id_recherche, categorie):
    try:
        rec = newminisab.recherche.get(newminisab.recherche.id == id_recherche)
        rec.id_sabnzbd = telechargement_sabnzbd(rec.article.title,
                                                rec.url, categorie)
        rec.save()
        return 'OK'
    except newminisab.article.DoesNotExist:
        abort(404)


@bp.route('/categorie/<int:id_categorie>')
def get_categorie(id_categorie=None):
    cat = newminisab.categorie.get(newminisab.categorie.id == id_categorie)
    if cat is not None:
        items = (newminisab.recuperer_tous_articles_pour_une_categorie(
                 cat.nom))
        return render_template('./categorie.html',
                               categorie=cat,
                               items=items)
    else:
        abort(404)


@bp.route('/categorie/liste')
def categorie_liste():
    listecategorie = newminisab.article.liste_categorie()
    return render_template('./barre_categorie.html', categorie=listecategorie)


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
                9000)
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
                9000)
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
                9000)
        r = requests.get(myurl, params=param)
        return r.status_code
    else:
        return 0


app = Flask(__name__)
app.register_blueprint(bp, prefix='/minisab')

if __name__ == "__main__":
    # app.run(host="0.0.0.0", port=9030)
    app.run()
