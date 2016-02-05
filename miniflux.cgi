#!/usr/bin/python3

import os, sys, cgi
#import cgitb
#cgitb.enable(display=0, logdir="./")
#sys.path.insert(0, '/volume1/homes/admin/python/')
import site
from ownmodule.miniflux import genere_fichier_html5_cgi

form = cgi.FieldStorage()
options = { opt : True if form.getvalue(opt) == 'oui' else False for opt in [ 'recherche', 'supprimercategoriemetal', 'supprimerfavoristermine' ] }

buffer = genere_fichier_html5_cgi('192.168.0.8', '192.168.0.8', form.getlist('resultat'), option = options)
#sys.stdout.buffer.write('Content-Type: text/html\r\n\r\n'.encode('utf-8'))
sys.stdout.buffer.write(buffer.encode('utf-8'))

