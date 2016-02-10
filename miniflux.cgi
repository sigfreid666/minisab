#!/usr/bin/python3

import os, sys, cgi
#import cgitb
#cgitb.enable(display=0, logdir="./")
#sys.path.insert(0, '/volume1/homes/admin/python/')
import site
from ownmodule.miniflux import genere_fichier_html5_cgi

liste_options = ( 'recherche', 'supprimercategoriemetal', 'supprimerfavoristermine' )
form = cgi.FieldStorage()
options = { }
for opt in liste_options:
    if not (form.getvalue(opt) is None):
        options[opt] = form.getvalue(opt)

buffer = genere_fichier_html5_cgi('192.168.0.8', '192.168.0.8', form.getlist('resultat'), option = options)
#sys.stdout.buffer.write('Content-Type: text/html\r\n\r\n'.encode('utf-8'))
sys.stdout.buffer.write(buffer.encode('utf-8'))

