from flask import Flask, Blueprint

import logging
import os

def create_app(mode):
	from . import settings

	logger = logging.getLogger(__name__)
	if mode == 'dev':
		logger.setLevel(logging.DEBUG)
	# handler = logging.FileHandler('/app/minisab.log')
	# handler.setLevel(logging.DEBUG)
	# handler.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s in %(module)s: %(message)s'))
	# logger.addHandler(handler)
	handler = logging.StreamHandler()
	handler.setLevel(logging.DEBUG)
	handler.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s in %(module)s: %(message)s'))
	logger.addHandler(handler)
	app = Flask(__name__, instance_relative_config=True)
	settings.init_config(app)
	
	from . import flaskminisab
	app.register_blueprint(flaskminisab.bp, url_prefix='/minisab')

	from . import newminisab
	newminisab.db.init(app.config['MINISAB_AUTRE_DBFILE'])

#current_app.config['MINISAB_DBFILE']
	return app

app = create_app('dev')