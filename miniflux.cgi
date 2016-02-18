#!/usr/bin/python3

import os, sys, cgi
import cgitb
cgitb.enable(display=0, logdir="./")
import site
from ownmodule.miniflux import genere_fichier_html5_cgi, supprimer_favoris

liste_options = ( 'recherche', 'supprimercategoriemetal', 'supprimerfavoristermine', 'testjava' )
form = cgi.FieldStorage()

if 'action' in form.keys():
    action = form.getvalue('action')
    sys.stdout.buffer.write('Content-Type: application/json\r\n\r\n'.encode('utf-8'))
    if action == 'supprimerfavoris':
        buffer = supprimer_favoris('192.168.0.8', '192.168.0.8', [{ 'miniflux' : form.getvalue('miniflux'), 'sab' : form.getvalue('sab')}])
else:
    buffer = genere_fichier_html5_cgi('192.168.0.8', '192.168.0.8', form.getlist('resultat'), option = {})
sys.stdout.buffer.write(buffer.encode('utf-8'))

