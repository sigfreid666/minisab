#!/usr/bin/python3

import os
import sys
import cgi
import pickle
#import cgitb
#cgitb.enable(display=0, logdir="./")
import site
import ownmodule
import json
from ownmodule import sabnzbd,sabnzbd_nc_cle_api
from ownmodule.miniflux import miniflux,ctx_miniflux

host_minifluxG = '192.168.0.8'
host_sabG = '192.168.0.8'

def lancer_telechargement_url(url, titre):
    # output['supprimer'].append({'id' : ids['miniflux']})
    sab = sabnzbd.sabnzbd(serveur=host_sabG, port=9000, cle_api=ownmodule.sabnzbd_nc_cle_api)
    resultat = sab.add_by_url(url, titre)
    # output = {'encours' : []}
    return resultat['result']

def supprimer_favoris(host_sab, host_miniflux, idminisab, port_sab=9000):
    output = {'supprimer': []}
    sab = sabnzbd.sabnzbd(serveur=host_sab, port=port_sab, cle_api=sabnzbd_nc_cle_api)
    mini = miniflux(host_miniflux)
    for ids in idminisab:
        if 'miniflux' in ids:
            jsdata, header = mini.supprimer_favoris(ids['miniflux'])
            output['supprimer'].append({'id': ids['miniflux']})
        if ('sab' in ids) and (not ids['sab'] is None):
            sab.delete_history(ids['sab'])
    return json.dumps(output)


def set_favoris(host_miniflux, liste_id):
    output = {'set': []}
    mini = miniflux(host_miniflux)
    for ids in liste_id:
        jsdata, header = mini.set_favoris(ids)
        output['set'].append({'id': ids})
    return json.dumps(output)

def genere_fichier_html5_cgi(host_sab, host_miniflux, option={}, port_sab=9000, debug=False):
    sab = sabnzbd.sabnzbd(serveur=host_sab, port=port_sab, cle_api=sabnzbd_nc_cle_api)
    if debug:
        print(sab)
    mini = miniflux(host_miniflux)
    ctx = ctx_miniflux()
    mini.get_favoris(sab)
    if os.access('recherche.bin', os.R_OK):
        with open('recherche.bin', 'rb') as fichier:
            for id_mini,analyse_taille in pickle.load(fichier).items():
                if id_mini in mini.new_favoris:
                    mini.new_favoris[id_mini].analyse_taille = analyse_taille
    if ('recherche' in option) and (option['recherche'] == 'oui'):
        mini.create_url_favoris(liste_nom_indexeur=['nzbindex', 'binsearch'])
        try:
            with open('recherche.bin', 'wb') as fichier:
                pickle.dump({id_mini: val.analyse_taille for id_mini,val in mini.new_favoris.items()}, fichier)
        except Exception as e:
            ctx.div.alone('Exception' + str(e), height='400px', width='100%')
    ctx.afficher_favoris([x[1] for x in mini.new_favoris.items()])
    return ctx.close()

form = cgi.FieldStorage()

if 'action' in form.keys():
    action = form.getvalue('action')
    sys.stdout.buffer.write('Content-Type: application/json\r\n\r\n'.encode('utf-8'))
    if action == 'supprimerfavoris':
        buffer = supprimer_favoris(host_minifluxG, '192.168.0.8', [{ 'miniflux' : form.getvalue('miniflux'), 'sab' : form.getvalue('sab')}])
    # elif action == 'telechargement':
    #     buffer = lancer_telechargement('192.168.0.8', [ (form.getvalue('id'), form.getvalue('titre')) ])
    elif action == 'telechargement_url':
        buffer = lancer_telechargement_url(form.getvalue('url'), form.getvalue('titre'))
    elif action == 'setfavoris':
        buffer = set_favoris(host_minifluxG, form.getvalue('miniflux').split(','))
else:
    buffer = genere_fichier_html5_cgi(host_minifluxG, '192.168.0.8', option = { 'recherche' : form.getvalue('recherche', 'non')})
sys.stdout.buffer.write(buffer.encode('utf-8'))

