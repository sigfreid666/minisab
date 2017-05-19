from flask import Flask, render_template
import newminisab

app = Flask(__name__)


@app.route("/")
def hello():
    articles = newminisab.recuperer_tous_articles()
    articles = [[x.title, x.taille, x.categorie] for x in articles]
    return render_template('./minifluxlist.html', titlepage='Miniflux',
                           items=articles)

if __name__ == "__main__":
    app.run()