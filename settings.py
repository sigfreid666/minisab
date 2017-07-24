import logging

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
        pass
