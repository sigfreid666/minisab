import logging
import os
import os.path
import json
import requests
import redis
from functools import wraps

log_config = {'version': 1, 'loggers': {'flaskminisab': {'level': 'INFO'},
                                        'newminisab': {'level': 'INFO'},
                                        '__main__': {'level': 'INFO'}}}

# 'handlers': {'sys': {'class': 'logging.handlers.SysLogHandler', 'address': ['192.168.0.8', 514]}}}
prefixe = "MINISAB_"
# obligatoire
dbfile, logfile, host_redis, port_redis = (None, None, None, None)
host_sabG, port_sabG, sabnzbd_nc_cle_api = (None, None, None)

logger = logging.getLogger('flaskminisab')


def make_url_sab(iconfig):
    return "http://%s:%s/sabnzbd/api" % (iconfig['host_sab'],
                                         iconfig['port_sab'])


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
        ret = None
        if host_redis is not None:
            red_iter = None
            config.config_file = './config.json'
            iconfig = config()
            if iconfig['host_redis'] is not None:
                red_iter = None
                try:
                    red_iter = redis.StrictRedis(host=iconfig['host_redis'],
                                                 port=iconfig['port_redis'])
                    ret = wrap(*args, red_iter=red_iter)
                except redis.exceptions.ConnectionError as e:
                    logging.error('Impossible de se connecter à Redis : %s', str(e))
        else:
            logger.info('redis non disponible')
        return ret
    return wrapper


def connexion_sab(wrap):
    @wraps(wrap)
    def wrapper(*args):
        config.config_file = './config.json'
        iconfig = config()
        myurl = make_url_sab(iconfig)
        if iconfig['host_sab'] is not None:
            try:
                return wrap(*args, sabnzbd_nc_cle_api=iconfig['cle_sab'],
                            url=myurl)
            except requests.exceptions.ConnectionError:
                logger.info('Impossible de se connecter a sabnzbd',
                            iconfig['host_sab'], iconfig['port_sab'])
                return {}
        else:
            logger.info('sabnzbd non disponible')
            return {}

    return wrapper


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
        self['port_redis'] = int(self['port_redis'])
        self['port_sab'] = int(self['port_sab'])

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
    a.init_config('toto.db', 'toto.log', 'redis', 8890, '192.168.0.8', 9000, '6f8af3c4c4487edf93d96979ed7d2321')
    a.sauver_config()
