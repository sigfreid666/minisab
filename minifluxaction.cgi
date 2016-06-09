#!c:/python34/python.exe
import os
import sys
import cgi
import site
import json
import ownmodule/miniflux

#form = cgi.FieldStorage()

#buffer = str(form.keys())

def setread(omini, oaction):
    omini.set_status_liste(oaction['liste_id'], oactio['status']):


liste_action = { 'setread' : set_read }
buffer = '{ "Resultat" : " PAS TROUVE" }'
js = json.load(sys.stdin)
mini = miniflux('192.168.0.8')
for action in js:
    if 'get' in action:
        if action['get'] == 'item':
            buffer = '{ "Resultat" : "TROUVE" }' 
    elif ('action' in action) and (action['action'] in liste_action:
        if liste_action[action['action']](mini, action)
sys.stdout.buffer.write('Content-Type: application/json\r\n\r\n'.encode('utf-8'))
sys.stdout.buffer.write(buffer.encode('utf-8'))

