# fonction utilitaire
from functools import wraps
from settings import host_redis, port_redis
import redis
import logging

redis_liste_urls = 'minisab_article_urls'
redis_urls = 'minisab_%d_urls'
redis_urls_encours = 'minisab_%d_urls_encours'
redis_urls_termine = 'minisab_%d_urls_termine'


def avec_redis(wrap):
    @wraps(wrap)
    def wrapper(*args):
        red_iter = None
        if host_redis is not None:
            red_iter = None
            try:
                red_iter = redis.StrictRedis(host=host_redis, port=port_redis)
            except redis.exceptions.ConnectionError as e:
                logging.error('Impossible de se connecter à Redis : %s', str(e))
        ret = wrap(red_iter, *args)
        return ret
    return wrapper

