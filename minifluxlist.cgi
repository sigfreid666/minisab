#!/usr/bin/python3

import os
import sys
#import cgi
#import cgitb
#cgitb.enable(display=0, logdir="./")
import site
from ownmodule.miniflux import generer_fichier_html_newsgroup

#form = cgi.FieldStorage()

buffer = generer_fichier_html_newsgroup('192.168.0.8')
sys.stdout.buffer.write(buffer.encode('utf-8'))

