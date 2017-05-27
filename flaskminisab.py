from flask import Flask, render_template, abort, redirect, url_for, Blueprint
import newminisab
# from ownmodule import sabnzbd, sabnzbd_nc_cle_api
import requests


categorie_preferee = ['Films HD']

bp = Blueprint('minisab', __name__, static_url_path='/minisab/static', static_folder='static')

@bp.route("/")
def index():
    print(url_for('static', filename='minisab.js'))
    print(url_for('minisab.static', filename='minisab.js'))
    articles, favoris = newminisab.recuperer_tous_articles_par_categorie()
    articles_preferes = [(x[0], len(x[1]), [x[1][y:y + 3] for y in range(0, len(x[1]), 3)])
                         for x in articles.items() if x[0] in categorie_preferee]
    articles = (articles_preferes +
                [(x[0], len(x[1]), [x[1][y:y + 3] for y in range(0, len(x[1]), 3)])
                 for x in articles.items() if x[0] not in categorie_preferee])
    # articles = [[x.title, x.taille, x.categorie] for x in articles]
    return render_template('./minifluxlist.html', titlepage='Miniflux',
                           articles=articles, favoris=favoris)


@bp.route('/article/<id_article>/favoris')
def marquer_article_favoris(id_article=None):
    try:
        ar = newminisab.article.get(newminisab.article.id == id_article)
        ar.favorie = True
        ar.lancer_recherche()
        ar.save()
        return render_template('./article.html', item=ar)
    except newminisab.article.DoesNotExist:
        abort(404)


@bp.route('/article/<id_article>/lu')
def marquer_article_lu(id_article=None):
    try:
        ar = newminisab.article.get(newminisab.article.id == id_article)
        ar.lu = True
        ar.save()
        return "OK"
    except newminisab.article.DoesNotExist:
        abort(404)


@bp.route('/article/<id_article>/recherche')
def recherche_article(id_article=None):
    try:
        ar = newminisab.article.get(newminisab.article.id == id_article)
        ar.lancer_recherche()
        return render_template('./article.html', item=ar)
    except newminisab.article.DoesNotExist:
        abort(404)


@bp.route('/recherche/<id_recherche>/telecharger')
def lancer_telecharger(id_recherche=None):
    try:
        rec = newminisab.recherche.get(newminisab.recherche.id == id_recherche)
        host_sabG = '192.168.0.8'
        sabnzbd_nc_cle_api = '6f8af3c4c4487edf93d96979ed7d2321'
        param = {'apikey': sabnzbd_nc_cle_api,
                 'output': 'json',
                 'mode': 'addurl',
                 'name': rec.url,
                 'nzbname': rec.article.title}
        myurl = "http://{0}:{1}/sabnzbd/api".format(
                host_sabG,
                9000)
        r = requests.get(myurl, params=param)
        # sab = sabnzbd.sabnzbd(serveur=host_sabG, port=9000, cle_api=sabnzbd_nc_cle_api)
        print(rec.url, rec.article.title)
        print(r.status_code)
        resultat = r.json()
        print(r.headers)
        if resultat['status']:
            print('status ok')
            rec.id_sabnzbd = resultat['nzo_ids'][0]
            rec.save()
        return 'OK'
    except newminisab.article.DoesNotExist:
        abort(404)


@bp.route('/categorie/<str_categorie>/lu')
def categorie_lu(str_categorie=None):
    cat = article.select().where(article.categorie == str_categorie)
    for x in cat:
        print(x.title)


app = Flask(__name__)
app.register_blueprint(bp, prefix='/minisab')

if __name__ == "__main__":
    # app.run(host="0.0.0.0", port=9030)
    app.run()
