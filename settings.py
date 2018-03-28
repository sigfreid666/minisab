import logging
import os

log_config = {'version': 1, 'loggers': {'flaskminisab': {'level': 'INFO'},
              'newminisab': {'level': 'INFO'},
              '__main__': {'level': 'INFO'}}}

# 'handlers': {'sys': {'class': 'logging.handlers.SysLogHandler', 'address': ['192.168.0.8', 514]}}}
prefixe = "MINISAB_"

# obligatoire
dbfile, logfile, host_redis, port_redis = (None, None, None, None)
host_sabG, port_sabG, sabnzbd_nc_cle_api = (None, None, None)

# d'abord on essaye de recuperer les variables d'environnement
config_tuple = ([None, "DBFILE"], [None, "LOGFILE"],
                [None, "HOST_REDIS"], [None, "PORT_REDIS"],
                [None, "HOST_SAB"], [None, "PORT_SAB"],    
                [None, "CLE_SAB"])

for c_tuple in config_tuple:
    c_tuple[0] = os.getenv(prefixe + c_tuple[1])
    # pas trouve dans les variables d'environnement
    if c_tuple[0] == None:
        logging.debug('setting : %s', c_tuple[1])

dbfile, logfile, host_redis, port_redis,\
host_sabG, port_sabG, sabnzbd_nc_cle_api = [x[0] for x in config_tuple]

port_redis = int(port_redis)
port_sabG = int(port_sabG)