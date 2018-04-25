# fichier de gestion de tout ce qui touche newsgroup
import logging
import requests
import redis
import os
from xml.dom.minidom import parseString
from xml.parsers.expat import ExpatError
from util import avec_redis
from util import redis_liste_urls, redis_urls
from util import redis_urls_encours, redis_urls_termine
from settings import acces_config
import itertools
from functools import wraps

logger = logging.getLogger('flaskminisab')


def filename_dump(id_article, indice=-1):
    return '/app/dump-%d-%s.nzb' % (id_article, str(indice) if indice >= 0 else 'concat')


def traitement_url(url, nom_fichier):
    try:
        logger.debug('Recuperation url %s', url)
        req = requests.get(url)
        content = req.text
        logger.debug('Taille fichier %d', len(content))
        if len(content) > 0:
            # on verifie la validite du fichier avant d'ecrire
            try:
                doc = parseString(content)
            except ExpatError as e:
                logger.error('Fichier nzb mal forme : url <%s>', url)
                return False
            finally:
                with open(nom_fichier, 'w') as fichier:
                    fichier.write(content)
                    return True
    except:
        return False


def traitement_nzb(liste_nom_fichier, nom_fichier_sortie):
    if len(liste_nom_fichier) == 0:
        return False
    content = ''
    try:
        with open(liste_nom_fichier[0], 'r') as fichier:
            content = fichier.read()
    except FileNotFoundError:
        logger.error('Fichier nzb non trouve : %s', liste_nom_fichier[0])
        return False
    logger.debug('Taille fichier %s : %d', liste_nom_fichier[0], len(content))
    doc = parseString(content)
    logger.debug('xml %s', doc.documentElement.tagName)
    logger.debug('Nombre de nodes : %d', len(doc.documentElement.childNodes))
    if doc.documentElement.tagName == 'nzb':
        for ajout_fichier in liste_nom_fichier[1:]:
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
        return True
    return False


@avec_redis
def merge_nzb(redis_iter, nombre_iteration=15):
    ret = {'article_encours': [], 'article_termine': []}
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
            nom_fichier = filename_dump(int_article_id,
                                        redis_iter.llen(redis_urls_termine % int_article_id))
            if traitement_url(url, nom_fichier):
                ret['article_encours'].append((int_article_id, nom_fichier))
                redis_iter.rpush(redis_urls_termine % int_article_id, nom_fichier)
                iteration += 1
            else:
                redis_iter.rpush(redis_urls_encours % int_article_id, url)
        nom_fichier_concat = concat_nzb(redis_iter, int_article_id)
        if nom_fichier_concat != '':
            ret['article_termine'].append((int_article_id, nom_fichier_concat))

    return ret


# @avec_redis
def concat_nzb(redis_iter, numero_article):
    logger.debug('concat_nzb')
    if ((redis_iter.llen(redis_urls % numero_article) > 0) or
            (redis_iter.llen(redis_urls % numero_article) > 0)):
        logger.debug('telechargement en cours pour %d', numero_article)
        return
    liste_nom_fichier = redis_iter.lrange(redis_urls_termine % numero_article, 0, -1)
    logger.debug('Article <%d>, nom fichier <%s>', numero_article, str(liste_nom_fichier))
    nom_fichier_concat = filename_dump(numero_article)
    if traitement_nzb(liste_nom_fichier, nom_fichier_concat):
        for fichier in liste_nom_fichier:
            os.remove(fichier)
        redis_iter.srem(redis_liste_urls, numero_article)
        redis_iter.ltrim(redis_urls % numero_article, 1, 0)
        redis_iter.ltrim(redis_urls_encours % numero_article, 1, 0)
        redis_iter.ltrim(redis_urls_termine % numero_article, 1, 0)
        redis_iter.delete(redis_urls % numero_article)
        redis_iter.delete(redis_urls_encours % numero_article)
        redis_iter.delete(redis_urls_termine % numero_article)
        return nom_fichier_concat
    return ''


@avec_redis
def nettoyage_traitement(redis_iter, numero_article):
    logger.debug('Nettoyage traitement %d', numero_article)
    if redis_iter.srem(redis_liste_urls, numero_article) == 1:
        liste_nom_fichier = redis_iter.lrange(redis_urls_termine % numero_article, 0, -1)
        for fichier in liste_nom_fichier:
            os.remove(fichier)
        redis_iter.ltrim(redis_urls % numero_article, 1, 0)
        redis_iter.ltrim(redis_urls_encours % numero_article, 1, 0)
        redis_iter.ltrim(redis_urls_termine % numero_article, 1, 0)
        redis_iter.delete(redis_urls % numero_article)
        redis_iter.delete(redis_urls_encours % numero_article)
        redis_iter.delete(redis_urls_termine % numero_article)


def connection_sab(iconfig):
    def connection_sab_wrap(wrap):
        @wraps(wrap)
        def wrapper(*args):
            if iconfig['host_sab'] is not None:
                try:
                    wrap(iconfig)
                except requests.exceptions.ConnectionError:
                    logger.info('Impossible de se connecter a sabnzbd',
                                iconfig['host_sab'], iconfig['port_sab'])
                    return {}
            else:
                logger.info('sabnzbd non disponible')
                return {}

            return wrapper
    return connection_sab_wrap


def make_url_sab(iconfig):
    return "http://%s:%s/sabnzbd/api" % (iconfig['host_sab'],
                                         iconfig['port_sab'])


@acces_config
@connection_sab(iconfig)
def status_sabnzbd(iconfig):
    param = {'apikey': iconfig['sabnzbd_nc_cle_api'],
             'output': 'json',
             'limit': '100',
             'mode': 'history'}
    myurl = make_url_sab(iconfig)
    r = requests.get(myurl, params=param)
    resultat = r.json()
    param = {'apikey': iconfig['sabnzbd_nc_cle_api'],
             'output': 'json',
             'mode': 'queue'}
    myurl = make_url_sab(iconfig)
    r = requests.get(myurl, params=param)
    resultat2 = r.json()
    resultat_total = itertools.chain(resultat['history']['slots'],
                                     resultat2['queue']['slots'])
    return {x['nzo_id']: x['status'] for x in resultat_total}


@acces_config
def telechargement_sabnzbd(iconfig, title, url, categorie):
    if host_sabG is not None:
        param = {'apikey': iconfig['sabnzbd_nc_cle_api'],
                 'output': 'json',
                 'mode': 'addurl',
                 'name': url,
                 'nzbname': title,
                 'cat': categorie}
        logger.debug('telechargement_sabnzbd : url <%s> title <%s>',
                     url, title)
        myurl = make_url_sab(iconfig)
        r = requests.get(myurl, params=param)
        resultat = r.json()
        logger.debug('telechargement_sabnzbd : status <%s>',
                     resultat['status'])
        if resultat['status']:
            logger.debug('telechargement_sabnzbd : nzo_ids <%s>',
                         str(resultat['nzo_ids']))
            return resultat['nzo_ids'][0]
        else:
            return ''
    else:
        return ''


if __name__ == '__main__':
    print(status_sabnzbd())
