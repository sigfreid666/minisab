from flask import Flask, Blueprint

import logging

def create_app():
	print('gogo')
	app = Flask(__name__)
	print('gogo')
	logger = app.logger # logging.getLogger('gunicorn.glogging.Logger')
	print('gogo')
	gunicorn_logger = logging.getLogger('gunicorn.error')
	print('gogo')
	app.logger.handlers = gunicorn_logger.handlers
	print('gogo1')
	app.config.from_object('minisab.settings.ConfigBase')
	print('gogo2')
	app.config.from_envvar('MINISAB_CONFIG', silent=False)
	print('gogo3')

	# bp = Blueprint('minisab', __name__, static_folder='/minisab/static')
	
	print('gogo')
	from . import flaskminisab
	app.register_blueprint(flaskminisab.bp, url_prefix='/minisab')

	from . import newminisab
	newminisab.db.init(app.config['MINISAB_DBFILE'])

#current_app.config['MINISAB_DBFILE']
	return app