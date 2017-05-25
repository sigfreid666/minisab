from flask import Flask, render_template, abort, redirect, url_for
import newminisab
from ownmodule import sabnzbd,sabnzbd_nc_cle_api

app = Flask(__name__)

categorie_preferee = ['Films HD']


@app.route("/")
def index():
    articles, favoris = newminisab.recuperer_tous_articles_par_categorie()
    articles_preferes = [(x[0], len(x[1]), [x[1][y:y + 3] for y in range(0, len(x[1]), 3)])
                         for x in articles.items() if x[0] in categorie_preferee]
    articles = (articles_preferes +
                [(x[0], len(x[1]), [x[1][y:y + 3] for y in range(0, len(x[1]), 3)])
                 for x in articles.items() if x[0] not in categorie_preferee])
    # articles = [[x.title, x.taille, x.categorie] for x in articles]
    return render_template('./minifluxlist.html', titlepage='Miniflux',
                           articles=articles, favoris=favoris)


@app.route('/article/<id_article>/favoris')
def marquer_article_favoris(id_article=None):
    try:
        ar = newminisab.article.get(newminisab.article.id == id_article)
        ar.favorie = True
        ar.lancer_recherche()
        ar.save()
        return render_template('./article.html', item=ar)
    except newminisab.article.DoesNotExist:
        abort(404)


@app.route('/article/<id_article>/lu')
def marquer_article_lu(id_article=None):
    try:
        ar = newminisab.article.get(newminisab.article.id == id_article)
        ar.lu = True
        ar.save()
        return redirect(url_for('index'))
    except newminisab.article.DoesNotExist:
        abort(404)


@app.route('/article/<id_article>/recherche')
def recherche_article(id_article=None):
    try:
        ar = newminisab.article.get(newminisab.article.id == id_article)
        ar.lancer_recherche()
        return render_template('./article.html', item=ar)
    except newminisab.article.DoesNotExist:
        abort(404)


@app.route('/recherche/<id_recherche>/telecharger')
def lancer_telecharger(id_recherche=None):
    try:
        host_sabG = '192.168.0.8'
        rec = newminisab.recherche.get(newminisab.recherche.id == id_recherche)
        sab = sabnzbd.sabnzbd(serveur=host_sabG, port=9000, cle_api=sabnzbd_nc_cle_api)
        print(rec.url, rec.article.title)
        sab.add_by_url(rec.url, rec.article.title)
        return 'OK'
    except newminisab.article.DoesNotExist:
        abort(404)


if __name__ == "__main__":
    app.run()
