import logging

log_config = {'version': 1, 'loggers': {'flaskminisab': {'level': 'INFO'},
              'newminisab': {'level': 'INFO'},
              '__main__': {'level': 'INFO'}}}

# 'handlers': {'sys': {'class': 'logging.handlers.SysLogHandler', 'address': ['192.168.0.8', 514]}}}

# obligatoire
try:
        from settings_local import dbfile, logfile, host_redis, port_redis
        from settings_local import host_sabG, sabnzbd_nc_cle_api

        logging.debug('setting : dbfile : %s', dbfile)
        logging.debug('setting : logfile : %s', logfile)
        logging.debug('setting : hostredis : %s', host_redis)
        logging.debug('setting : port_redis : %s', port_redis)
        logging.debug('setting : host_sabG : %s', host_sabG)
        logging.debug('setting : sabnzbd_nc_cle_api : %s', sabnzbd_nc_cle_api)
except ImportError as e:
        logging.error('Impossible d''importer le settings local : %s', str(e))

# facultatif
try:
        from settings_local import log_config
        logging.debug('setting : log_config : %s', log_config)
except ImportError as e:
        pass
