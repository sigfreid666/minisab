from flask import Flask
import logging

__version__ = "2.12"


def create_app(mode=""):
    from . import settings

    logger = logging.getLogger(__name__)
    if mode == "dev":
        logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    if mode == "dev":
        handler.setLevel(logging.DEBUG)
    handler.setFormatter(
        logging.Formatter(
            "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
        )
    )
    logger.addHandler(handler)
    app = Flask(__name__, instance_relative_config=True)
    settings.init_config(app)

    from . import flaskminisab

    app.register_blueprint(flaskminisab.bp, url_prefix="/minisab")

    from . import newminisab

    newminisab.db.init(app.config["MINISAB_AUTRE_DBFILE"])

    return app

