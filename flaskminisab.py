from flask import Flask, render_template, abort, redirect, url_for, Blueprint, request
import newminisab
# from ownmodule import sabnzbd, sabnzbd_nc_cle_api
import requests
import logging
import itertools
from peewee import fn

categorie_preferee = ['Films HD']
host_sabG = '192.168.0.8'
sabnzbd_nc_cle_api = '6f8af3c4c4487edf93d96979ed7d2321'
version = '2.1'
bp = Blueprint('minisab', __name__, static_url_path='/minisab/static', static_folder='static')


@bp.route("/")
def index():
    articles, favoris = newminisab.recuperer_tous_articles_par_categorie()
    newminisab.logger.info('index, articles %d, favoris %d', len(articles), len(favoris))
    status_sab = status_sabnzbd()
    newminisab.logger.info('index, statut sab %s', str(status_sab))
    for x in favoris:
        for y in x.recherche_resultat:
            newminisab.logger.info('index, title %s, id sab %s', x.title, y.id_sabnzbd)
            if y.id_sabnzbd in status_sab:
                x.status_sabnzbd = status_sab[y.id_sabnzbd]
                newminisab.logger.info('index, trouve %s', x.status_sabnzbd)
    id_categorie = 1
    articles_preferes = [(x[0], len(x[1]), x[1], x[0].replace('/', '_'))
                         for x in articles.items() if x[0] in categorie_preferee]
    articles = (articles_preferes +
                [(x[0], len(x[1]), x[1], x[0].replace('/', '_'))
                 for x in articles.items() if x[0] not in categorie_preferee])
    # articles = [[x.title, x.taille, x.categorie] for x in articles]
    return render_template('./minifluxlist.html', titlepage='Miniflux',
                           articles=articles, favoris=favoris,
                           categorie_sabnzbd=[x[0] for x in newminisab.categorie_sabnzbd],
                           version=version)


@bp.route('/article/<id_article>/favoris')
def marquer_article_favoris(id_article=None):
    try:
        ar = newminisab.article.get(newminisab.article.id == id_article)
        ar.favorie = True
        ar.lancer_recherche()
        newminisab.logger.info('marquer favoris %d nb recherche %d', id_article, len(ar.recherche_resultat))
        ar.save()
        return render_template('./article.html', item=ar,
                               categorie_sabnzbd=[x[0] for x in newminisab.categorie_sabnzbd])
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
                for y in ar.recherche_resultat:
                    newminisab.logger.info('article_lu, title %s, id sab %s', ar.title, y.id_sabnzbd)
                    if y.id_sabnzbd != '': 
                        delete_history_sab(y.id_sabnzbd)
                ar.save()
        return "OK"
    except newminisab.article.DoesNotExist:
        abort(404)


@bp.route('/article/<id_article>/recherche')
def recherche_article(id_article=None):
    try:
        ar = newminisab.article.get(newminisab.article.id == id_article)
        ar.lancer_recherche()
        return render_template('./article.html', item=ar,
                               categorie_sabnzbd=[x[0] for x in newminisab.categorie_sabnzbd])
    except newminisab.article.DoesNotExist:
        abort(404)


@bp.route('/recherche/<id_recherche>/telecharger/<categorie>')
@bp.route('/recherche/<id_recherche>/telecharger/', defaults={'categorie': '*'})
def lancer_telecharger(id_recherche, categorie):
    try:
        rec = newminisab.recherche.get(newminisab.recherche.id == id_recherche)
        rec.id_sabnzbd = telechargement_sabnzbd(rec.article.title, rec.url, categorie)
        rec.save()
        return 'OK'
    except newminisab.article.DoesNotExist:
        abort(404)


@bp.route('/categorie/<str_categorie>/lu')
def categorie_lu(str_categorie=None):
    cat = newminisab.article.select().where(newminisab.article.categorie == str_categorie)
    for x in cat:
        print(x.title)
    return 'OK'

@bp.route('/categorie/liste')
def categorie_liste():
    listecategorie = newminisab.article.liste_categorie()
    return render_template('./barre_categorie.html', categorie=listecategorie)

def telechargement_sabnzbd(title, url, categorie):
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

def status_sabnzbd():
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
        return {x['nzo_id']: x['status'] for x in itertools.chain(resultat['history']['slots'], resultat2['queue']['slots'])}
    except requests.exceptions.ConnectionError:
        return {}


def delete_history_sab(id_sab):
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


app = Flask(__name__)
app.register_blueprint(bp, prefix='/minisab')

if __name__ == "__main__":
    # app.run(host="0.0.0.0", port=9030)
    app.run()
