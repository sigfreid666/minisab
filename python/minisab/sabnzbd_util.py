# fichier de gestion de tout ce qui touche newsgroup
import logging
import requests
import redis
import os
from xml.dom.minidom import parseString
from xml.parsers.expat import ExpatError
from minisab.settings import connexion_sab, connexion_redis
import itertools
from functools import wraps

nom_cat_sab = 'minisab_categorie_sabnzbd'
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

status_possibleG = ('Completed', 'Failed', 'Downloading', 'Queued')
redis_liste_urls = 'minisab_article_urls'
redis_urls = 'minisab_%d_urls'
redis_urls_encours = 'minisab_%d_urls_encours'
redis_urls_termine = 'minisab_%d_urls_termine'


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
                parseString(content)
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


@connexion_redis
def merge_nzb(nombre_iteration=15, redis_iter=None):
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
        nom_fichier_concat = concat_nzb(int_article_id,
                                        redis_iter=redis_iter)
        if nom_fichier_concat != '':
            ret['article_termine'].append((int_article_id, nom_fichier_concat))

    return ret


# @avec_redis
def concat_nzb(numero_article, redis_iter=None):
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


@connexion_redis
def nettoyage_traitement(numero_article, redis_iter=None):
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


@connexion_sab
def status_sabnzbd(sabnzbd_nc_cle_api='', url=''):
    param = {'apikey': sabnzbd_nc_cle_api,
             'output': 'json',
             'limit': '100',
             'mode': 'history'}
    logger.debug('Url : %s, %s', url, str(param))
    r = requests.get(url, params=param)
    resultat = r.json()
    logger.debug('Resultat : %d', len(resultat['history']['slots']))
    param = {'apikey': sabnzbd_nc_cle_api,
             'output': 'json',
             'mode': 'queue'}
    logger.debug('Url : %s, %s', url, str(param))
    r = requests.get(url, params=param)
    resultat2 = r.json()
    logger.debug('Resultat2 : %d', len(resultat2['queue']['slots']))
    resultat_total = itertools.chain(resultat['history']['slots'],
                                     resultat2['queue']['slots'])
    return {x['nzo_id']: x['status'] for x in resultat_total}


@connexion_sab
def telechargement_sabnzbd(title, url_tel, categorie,
                           sabnzbd_nc_cle_api='', url=''):
    param = {'apikey': sabnzbd_nc_cle_api,
             'output': 'json',
             'mode': 'addurl',
             'name': url_tel,
             'nzbname': title,
             'cat': categorie}
    logger.debug('telechargement_sabnzbd : url <%s> title <%s>',
                 url_tel, title)
    r = requests.get(url, params=param)
    resultat = r.json()
    logger.debug('telechargement_sabnzbd : status <%s>',
                 resultat['status'])
    if resultat['status']:
        logger.debug('telechargement_sabnzbd : nzo_ids <%s>',
                     str(resultat['nzo_ids']))
        return {'nzo_ids': resultat['nzo_ids'][0]}
    else:
        return {}


@connexion_sab
def delete_history_sab(id_sab,
                       sabnzbd_nc_cle_api='', url=''):
    param = {'apikey': sabnzbd_nc_cle_api,
             'output': 'json',
             'name': 'delete',
             'value': id_sab,
             'mode': 'history'}
    r = requests.get(url, params=param)
    return {'status': r.status_code}


@connexion_redis
def get_categorie_redis(red_iter=None):
    logger.debug('get_categorie_redis : redis %s', str(red_iter))
    ret = [x.decode('utf-8')
           for x in red_iter.lrange(nom_cat_sab, 0, -1)]
    logger.debug('get_categorie_redis : %s', str(ret))
    return ret


@connexion_redis
def set_categorie_redis(categories, red_iter=None):
    logger.debug('set_categorie_redis : redis %s', str(red_iter))
    red_iter.lpush(nom_cat_sab, *[x.encode('ascii')
                                  for x in categories])
    red_iter.expire(nom_cat_sab, 600)


@connexion_sab
def get_categorie_sabnzbd(sabnzbd_nc_cle_api='', url=''):
    categorie_sabnzbd = get_categorie_redis()
    if len(categorie_sabnzbd) == 0:
        param = {'apikey': sabnzbd_nc_cle_api,
                 'output': 'json',
                 'mode': 'get_cats'}
        r = requests.get(url, params=param)
        resultat = r.json()
        if 'categories' in resultat:
            set_categorie_redis(resultat['categories'])
            return resultat['categories']
        else:
            return ''
    else:
        return categorie_sabnzbd


@connexion_redis
def check_sabnzbd(red_iter=None):
    status = {'resultat': False}
    logger.debug('check_sabnzbd')
    st_sb = status_sabnzbd()
    if len(st_sb) > 0:
        for status in status_possibleG:
            members = red_iter.smembers('sab_' + status)
            if len(members) > 0:
                red_iter.srem('sab_' + status, *members)
    logger.debug('check_sabnzbd : %s', str(st_sb))
    for idsab, status in st_sb.items():
        if status in status_possibleG:
            red_iter.sadd('sab_' + status, idsab)
        else:
            logger.info('Status ignore : %s', status)
    status = {'resultat': True, 'nb_result': len(st_sb)}
    return status


@connexion_redis
def get_status_sab_redis(red_iter=None):
    status_sab = {}
    for status in status_possibleG:
        for elem in red_iter.smembers('sab_' + status):
            status_sab[elem.decode()] = status
    return status_sab


@connexion_redis
def get_info_affiche_urls(red_iter=None):
    logger.info('Affichage des urls')
    num_art = [x.decode() for x in red_iter.smembers(util.redis_liste_urls)]
    table_urls = []
    for x in num_art:
        for y in (util.redis_urls % int(x),
                  util.redis_urls_termine % int(x),
                  util.redis_urls_encours % int(x)):
            i = 0
            table_urls.append((y, []))
            for z in red_iter.lrange(y, 0, -1):
                table_urls[-1][1].append((i, z))
                i += 1

    logger.debug('Liste article %s', str(num_art))
    logger.debug('Liste urls %s', str(table_urls))
    return num_art, table_urls


@connexion_redis
def save_urls(red_iter, num_article, urls):
    red_iter.sadd(util.redis_liste_urls, num_article)
    if red_iter.exists(util.redis_urls % num_article):
        logger.debug('%s existe', util.redis_urls % num_article)
        red_iter.ltrim(util.redis_urls_encours % num_article, 1, 0)
        red_iter.ltrim(util.redis_urls_termine % num_article, 1, 0)
        red_iter.ltrim(util.redis_urls % num_article, 1, 0)
        # red_iter.delete(util.redis_urls_encours % num_article)
        # red_iter.delete(util.redis_urls_termine % num_article)
        # red_iter.delete(util.redis_urls % num_article)
    red_iter.lpush(util.redis_urls % num_article, *urls)


if __name__ == '__main__':
    # a = status_sabnzbd()
    # print(a)
    # print(delete_history_sab('SABnzbd_nzo_gqKhUi'))
    print('start')
    print(check_sabnzbd())
    # print(get_categorie_sabnzbd())
