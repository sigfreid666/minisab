from flask import Flask, render_template, abort
import newminisab

app = Flask(__name__)

categorie_preferee = ['Films HD']


@app.route("/")
def hello():
    articles = newminisab.recuperer_tous_articles_par_categorie()
    favoris = [z for x, y in articles.items() for z in y if z.favorie]
    articles_preferes = [(x[0], len(x[1]), [x[1][y:y + 3] for y in range(0, len(x[1]), 3)])
                         for x in articles.items() if x[0] in categorie_preferee]
    articles = (articles_preferes +
                [(x[0], len(x[1]), [x[1][y:y + 3] for y in range(0, len(x[1]), 3)])
                 for x in articles.items() if x[0] not in categorie_preferee])
    print(articles)
    # articles = [[x.title, x.taille, x.categorie] for x in articles]
    return render_template('./minifluxlist.html', titlepage='Miniflux',
                           articles=articles, favoris=favoris)


@app.route('/article/<id_article/favoris')
def marquer_article_favoris(id_article=None):
    try:
        ar = newminisab.article.get(newminisab.article.guid == id_article)
        ar.favorie = True
        ar.save()
    except newminisab.article.DoesNotExist:
        abort(404)
if __name__ == "__main__":
    app.run()
