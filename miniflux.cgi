#!/usr/bin/python3

import os, sys, cgi
#import cgitb
#cgitb.enable(display=0, logdir="./")
import site
import ownmodule
from ownmodule import sabnzbd
from ownmodule.miniflux import genere_fichier_html5_cgi, supprimer_favoris, lancer_telechargement,set_favoris


def lancer_telechargement_url(url, titre):
    # output['supprimer'].append({'id' : ids['miniflux']})
    sab = sabnzbd.sabnzbd(serveur='192.168.0.8', port=9000, cle_api=ownmodule.sabnzbd_nc_cle_api)
    resultat = sab.add_by_url(url, titre)
    # output = {'encours' : []}
    return resultat['result']

liste_options = ( 'recherche', 'supprimercategoriemetal', 'supprimerfavoristermine', 'testjava' )
form = cgi.FieldStorage()

if 'action' in form.keys():
    action = form.getvalue('action')
    sys.stdout.buffer.write('Content-Type: application/json\r\n\r\n'.encode('utf-8'))
    if action == 'supprimerfavoris':
        buffer = supprimer_favoris('192.168.0.8', '192.168.0.8', [{ 'miniflux' : form.getvalue('miniflux'), 'sab' : form.getvalue('sab')}])
    elif action == 'telechargement':
        buffer = lancer_telechargement('192.168.0.8', [ (form.getvalue('id'), form.getvalue('titre')) ])
    elif action == 'telechargement_url':
        buffer = lancer_telechargement_url(form.getvalue('url'), form.getvalue('titre'))
    elif action == 'setfavoris':
        buffer = set_favoris('192.168.0.8', form.getvalue('miniflux').split(','))
else:
    buffer = genere_fichier_html5_cgi('192.168.0.8', '192.168.0.8', form.getlist('resultat'), option = { 'recherche' : form.getvalue('recherche', 'non')})
sys.stdout.buffer.write(buffer.encode('utf-8'))

