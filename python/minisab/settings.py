import logging
import os
import os.path
import json
import requests
import redis
from functools import wraps
from flask import current_app

log_config = {'version': 1, 'loggers': {'flaskminisab': {'level': 'INFO'},
                                        'newminisab': {'level': 'INFO'},
                                        '__main__': {'level': 'INFO'}}}

# 'handlers': {'sys': {'class': 'logging.handlers.SysLogHandler', 'address': ['192.168.0.8', 514]}}}
prefixe = "MINISAB_"
# obligatoire
dbfile, logfile, host_redis, port_redis = (None, None, None, None)
host_sabG, port_sabG, sabnzbd_nc_cle_api = (None, None, None)

logger = logging.getLogger('minisab')


def make_url_sab(host, port):
    return "http://%s:%s/sabnzbd/api" % (host, port)


def acces_config_avec_sab(wrap):
    @wraps(wrap)
    def wrapper(*args):
        config.config_file = './config.json'
        iconfig = config()
        ret = wrap(iconfig, *args)
        return ret
    return wrapper


def connexion_redis(wrap):
    @wraps(wrap)
    def wrapper(*args):
        ret = {}
        if current_app.config['MINISAB_REDIS_CNX']:
            red_iter = None
            try:
                red_iter = redis.StrictRedis(host=current_app.config['MINISAB_REDIS_HOST'],
                                             port=current_app.config['MINISAB_REDIS_PORT'])
                ret = wrap(*args, red_iter=red_iter)
            except redis.exceptions.ConnectionError as e:
                logger.error('Impossible de se connecter à Redis : %s', str(e))
        else:
            logger.warning('redis non disponible')
        return ret
    return wrapper


def connexion_sab(wrap):
    @wraps(wrap)
    def wrapper(*args):
        if current_app.config['MINISAB_SAB_CNX']:
            try:
                myurl = make_url_sab(current_app.config['MINISAB_SAB_HOST'],
                                     current_app.config['MINISAB_SAB_PORT'])
                return wrap(*args, sabnzbd_nc_cle_api=current_app.config['MINISAB_SAB_CLE'],
                            url=myurl)
            except requests.exceptions.ConnectionError as e:
                logger.error('Impossible de se connecter a sabnzbd %s:%d, %s',
                            current_app.config['MINISAB_SAB_HOST'],
                            current_app.config['MINISAB_SAB_PORT'], str(e))
                return {}
        else:
            logger.warning('sabnzbd non disponible')
            return {}

    return wrapper

def init_config(app):
    app.config.from_object('minisab.settings.ConfigBase')
    for key in ConfigBase.MINISABINV_AUTRE_CONFIG:
        if app.config.from_pyfile(key, silent=False):
            logger.info('Chargement configuration de %s : %s', key, ConfigBase.strConfig(app.config))

    if ConfigBase.MINISABINV_CONFIG_FILE is not None:
        app.config.from_json(ConfigBase.MINISABINV_CONFIG_FILE, silent=True)        
        logger.info('Chargement configuration json %s : %s', ConfigBase.MINISABINV_CONFIG_FILE,
                    ConfigBase.strConfig(app.config))


class ConfigBase:
    _prefix_invariant = 'MINISABINV_'
    _prefix = 'MINISAB_'
    _suffixe_active = 'CNX'
    _sousprefix = (('MINISAB_REDIS_', 'Redis'),
                   ('MINISAB_SAB_', 'Sabnzbd'),
                   ('MINISAB_AUTRE_', 'Autre'))
    MINISAB_REDIS_CNX = False
    MINISAB_REDIS_HOST = None
    MINISAB_REDIS_PORT = 0
    MINISAB_SAB_CNX = False
    MINISAB_SAB_HOST = None
    MINISAB_SAB_PORT = 0
    MINISAB_SAB_CLE = None
    MINISAB_AUTRE_DBFILE = None if 'MINISAB_AUTRE_DBFILE' not in os.environ else os.environ['MINISAB_AUTRE_DBFILE']
    MINISAB_AUTRE_LOGFILE = None if 'MINISAB_AUTRE_LOGFILE' not in os.environ else os.environ['MINISAB_AUTRE_LOGFILE']
    MINISABINV_AUTRE_CONFIG = [] if 'MINISABINV_AUTRE_CONFIG' not in os.environ else os.environ['MINISABINV_AUTRE_CONFIG'].split(';')
    MINISABINV_CONFIG_FILE = None if 'MINISABINV_CONFIG_FILE' not in os.environ else os.environ['MINISABINV_CONFIG_FILE']

    def __init__(self, app):
        for attr in app.config:
            if attr.startswith(self._prefix):
                setattr(self, attr.upper(), app.config[attr])
        logger.debug('__init__ : %s', str(self))

    def maj_config(self, data):
        logger.debug('data : %s', str(data))
        diff = {}
        # mis a False de tous les attributs bool
        # ils seront mis a true par data
        for attr in dir(self):
            if (attr.startswith(self._prefix) and
                (type(getattr(self, attr)) == bool)):
                setattr(self, attr, False)
                diff[attr] = getattr(self, attr)
        for attr in data:
            attribut = attr.upper()
            # value = getattr(self, attribut)
            if type(getattr(self, attribut)) == bool:
                setattr(self, attribut, True)
            elif type(getattr(self, attribut)) == int:
                setattr(self, attribut, int(data[attr]))
            else:
                setattr(self, attribut, data[attr])
            # newvalue = getattr(self, attribut)
            # if value != newvalue:
            diff[attribut] = getattr(self, attribut)
        logger.debug('maj_config : %s', str(self))
        if ((self.MINISABINV_CONFIG_FILE is not None) and
            (len(diff) > 0)):
            logger.debug('Ecriture json : %s', str(diff))
            with open(self.MINISABINV_CONFIG_FILE, 'w') as fichier_json:
                json.dump(diff, fichier_json)
        return self

    @classmethod
    def get_config(cls, app):
        config_app = []
        for souspref, libelle in cls._sousprefix:
            values = app.config.get_namespace(souspref)
            if cls._suffixe_active.lower() in values:
                act = values[cls._suffixe_active.lower()]
                del values[cls._suffixe_active.lower()]
                config_app.append(((libelle, act, souspref), values))
            else:
                config_app.append(((libelle, None, souspref), values))

        logger.debug('config_app : %s', str(config_app))
        # for libelle, x in config_app:
        #     logger.debug('%s', str(libelle))
        #     for y in x:
        #         logger.debug('%s : %s', y, str(type(x[y])))
        return config_app

    @classmethod
    def strConfig(cls, dictconfig):
        r = ''
        for x in dictconfig:
            if x.startswith(cls._prefix):
                r = r + '(<%s> = <%s>)' % (x, dictconfig[x])
        return r                

    def __str__(self):
        r = ''
        for x in dir(self):
            if x.startswith(self._prefix):
                r = r + '(<%s> = <%s>)' % (x, getattr(self, x))
        return r


class config(dict):
    config_file = '/data/config.json'
    config_json = ("dbfile", "logfile",
                   "host_redis", "port_redis",
                   "host_sab", "port_sab",
                   "cle_sab")
    ident = 'minisab1.0'

    def __init__(self, init_from_env=True):
        super().__init__(self)
        if (not self.charger_config()) and init_from_env:
            self.init_config_from_env()

    def init_config_from_env(self):
        config_tuple = ([None, "DBFILE"], [None, "LOGFILE"],
                        [None, "HOST_REDIS"], [None, "PORT_REDIS"],
                        [None, "HOST_SAB"], [None, "PORT_SAB"],
                        [None, "CLE_SAB"])

        for c_tuple in config_tuple:
            c_tuple[0] = os.getenv(prefixe + c_tuple[1])
            # pas trouve dans les variables d'environnement
            if c_tuple[0] is None:
                logging.debug('setting : %s', c_tuple[1])

        self.update([(x[1].lower(), x[0]) for x in config_tuple])
        try:
            self['port_sab'] = int(self['port_sab'])
        except TypeError:
            self['port_sab'] = 0
        try:
            self['port_redis'] = int(self['port_redis'])
        except TypeError:
            self['port_redis'] = 0

    def init_config(self, dbfile, logfile, host_redis, port_redis,
                    host_sab, port_sab, cle_sab):
        self['dbfile'] = dbfile
        self['logfile'] = logfile
        self['host_redis'] = host_redis
        self['port_redis'] = port_redis
        self['host_sab'] = host_sab
        self['port_sab'] = port_sab
        self['cle_sab'] = cle_sab

    def charger_config(self):
        if os.path.exists(self.config_file):
            logging.debug('file config exist')
            with open(self.config_file, mode='r') as config_file:
                json_data = json.load(config_file)
                logging.debug('json %s', str(json_data))
                if self.ident not in json_data:
                    raise Exception('identifiant non trouve dans config')
                else:
                    self.update(json_data[self.ident])
            return True
        return False

    def sauver_config(self):
        with open(self.config_file, mode='w') as config_file:
            json_data = {self.ident: self}
            json.dump(json_data, config_file, indent=0)
            logging.debug('ecriture fichier config')


if __name__ == '__main__':
    config.config_file = './config.json'
    a = config(init_from_env=False)
    a.init_config('toto.db', 'toto.log', 'localhost', 6379, '192.168.0.8', 9000, '6f8af3c4c4487edf93d96979ed7d2321')
    a.sauver_config()
