# fichier de gestion de tout ce qui touche newsgroup
import logging
import requests
import redis
from xml.dom.minidom import parseString
from util import avec_redis
from util import redis_liste_urls, redis_urls
from util import redis_urls_encours, redis_urls_termine

logger = logging.getLogger('flaskminisab')


def traitement_url(url, nom_fichier):
    try:
        logger.debug('Recuperation url %s', url)
        req = requests.get(url)
        content = req.text
        logger.debug('Taille fichier %d', len(content))
        if len(content) > 0:
            with open(nom_fichier, 'w') as fichier:
                fichier.write(content)
                return True
    except:
        return False


def traitement_nzb(nom_fichier, nom_fichier_autre, nom_fichier_sortie):
    content = ''
    with open(nom_fichier, 'r') as fichier:
        content = fichier.read()
    logger.debug('Taille fichier %s : %d', nom_fichier, len(content))
    doc = parseString(content)
    logger.debug('xml %s', doc.documentElement.tagName)
    logger.debug('Nombre de nodes : %d', len(doc.documentElement.childNodes))
    if doc.documentElement.tagName == 'nzb':
        for ajout_fichier in nom_fichier_autre:
            with open(ajout_fichier, 'r') as fichier:
                ajout_content = fichier.read()
            logger.debug('Taille fichier %s : %d', ajout_fichier, len(ajout_content))
            ajout_doc = parseString(ajout_content)
            logger.debug('Nombre de nodes : %d', len(ajout_doc.documentElement.childNodes))
            int_node = 0
            for child in ajout_doc.documentElement.childNodes:
                if ((child.nodeType == child.ELEMENT_NODE) and
                    (child.tagName == 'file')):
                    doc.documentElement.appendChild(child)
                    int_node += 1
            logger.debug('Nombre de nodes : %d', int_node)
    logger.debug('Nombre de nodes : %d', len(doc.documentElement.childNodes))
    with open(nom_fichier_sortie, mode='w') as fichier:
        doc.writexml(fichier)



@avec_redis
def merge_nzb(redis_iter, nombre_iteration=5):
    # res = red_iter.lrange(nom_cat_sab, 0, -1)
    # logger.debug('Redis : %s', str(res))
    ret = {'article_id': []}
    logger.debug('merge_nzb')
    # d'abord on essaye de checker les urls en cours
    iteration = 0
    for article_id in redis_iter.smembers(redis_liste_urls):
        int_article_id = int(article_id)
        taille_en_cours = redis_iter.llen(redis_urls_encours % int_article_id)
        if taille_en_cours < nombre_iteration:
            for i in range(nombre_iteration - taille_en_cours):
                redis_iter.rpoplpush(redis_urls % int_article_id,
                                     redis_urls_encours % int_article_id)
        for i_url in range(nombre_iteration):
            url = redis_iter.lpop(redis_urls_encours % int_article_id)
            if url is None:
                break
            logger.debug('En cours article %d, url %s', int_article_id, url)
            nom_fichier = '/app/dump-%d-%d.xml' % (int_article_id,
                                                   redis_iter.llen(redis_urls_termine % int_article_id))
            if traitement_url(url, nom_fichier):
                ret['article_id'].append((int_article_id, nom_fichier))
                redis_iter.rpush(redis_urls_termine % int_article_id, nom_fichier)
                iteration += 1

    return ret


@avec_redis
def concat_nzb(redis_iter):
    logger.debug('concat_nzb')
    for article_id in redis_iter.smembers(redis_liste_urls):
        int_article_id = int(article_id)
        nom_fichier = redis_iter.lindex(redis_urls_termine % int_article_id, 0)
        logger.debug('Article <%d>, nom fichier <%s>', int_article_id, nom_fichier)
        nom_fichier_autre = redis_iter.lindex(redis_urls_termine % int_article_id, 1)
        logger.debug('Article <%d>, nom fichier <%s>', int_article_id, nom_fichier_autre)
        traitement_nzb(nom_fichier, [nom_fichier_autre], '/app/dump_concat.nzb')
