from flask import Flask, render_template
import newminisab

app = Flask(__name__)


@app.route("/")
def hello():
    articles = newminisab.recuperer_tous_articles_par_categorie()
    for x in articles:
        articles[x] = [articles[x][y:y + 3] for y in range(0, len(articles[x]), 3)]
    print(articles)
    # articles = [[x.title, x.taille, x.categorie] for x in articles]
    return render_template('./minifluxlist.html', titlepage='Miniflux',
                           cat_items=articles)

if __name__ == "__main__":
    app.run()