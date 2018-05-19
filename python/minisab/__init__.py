from flask import Flask, Blueprint

import logging
import os

def create_app(mode):
	from logging.config import dictConfig

	logger = logging.getLogger(__name__)
	logger.setLevel(logging.DEBUG)
	# handler = logging.FileHandler('/app/minisab.log')
	# handler.setLevel(logging.DEBUG)
	# handler.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s in %(module)s: %(message)s'))
	# logger.addHandler(handler)
	handler = logging.StreamHandler()
	handler.setLevel(logging.DEBUG)
	handler.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s in %(module)s: %(message)s'))
	logger.addHandler(handler)
	app = Flask(__name__)
	app.config.from_object('minisab.settings.ConfigBase')
	if app.config.from_envvar('MINISAB_CONFIG', silent=False):
		logger.info('Chargement configuration de MINISAB_CONFIG')
		logger.info('MINISAB_DBFILE = %s', app.config['MINISAB_DBFILE'])
		logger.info('MINISAB_LOGFILE = %s', app.config['MINISAB_LOGFILE'])
		logger.info('MINISAB_HOST_REDIS = %s', app.config['MINISAB_HOST_REDIS'])
		logger.info('MINISAB_PORT_REDIS = %d', app.config['MINISAB_PORT_REDIS'])
		logger.info('MINISAB_HOST_SAB = %s', app.config['MINISAB_HOST_SAB'])
		logger.info('MINISAB_PORT_SAB = %d', app.config['MINISAB_PORT_SAB'])
		logger.info('MINISAB_CLE_SAB = %s', app.config['MINISAB_CLE_SAB'])
		logger.info('MINISAB_CONFIG_FILE = %s', app.config['MINISAB_CONFIG_FILE'])
	else:
		print('erreur Chargement configuration de MINISAB_CONFIG')
		logger.warning('Impossible de charger configuration de MINISAB_CONFIG : %s',
					   os.environ['MINISAB_CONFIG'] if 'MINISAB_CONFIG' in os.environ else '<non_definie>')

	from . import flaskminisab
	app.register_blueprint(flaskminisab.bp, url_prefix='/minisab')

	from . import newminisab
	newminisab.db.init(app.config['MINISAB_DBFILE'])

#current_app.config['MINISAB_DBFILE']
	return app

app = create_app('dev')