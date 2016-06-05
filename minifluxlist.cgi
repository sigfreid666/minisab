#!/usr/bin/python3

import os
import sys
import cgi
#import cgitb
#cgitb.enable(display=0, logdir="./")
import site
from ownmodule.miniflux import generer_fichier_html_newsgroup
from ownmodule.miniflux import miniflux

form = cgi.FieldStorage()

if 'action' in form.keys():
        mini = miniflux('192.168.0.8')
        mini.set_status_liste(form.getvalue('id').split(','))
        buffer = 'OK'
else:
        buffer = generer_fichier_html_newsgroup('192.168.0.8')
sys.stdout.buffer.write(buffer.encode('utf-8'))

