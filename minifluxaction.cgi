#!c:/python34/python.exe
import os
import sys
import cgi
import site
import json

#form = cgi.FieldStorage()

#buffer = str(form.keys())
buffer = '{ "Resultat" : " PAS TROUVE" }'
js = json.load(sys.stdin)
for action in js:
    if 'get' in action:
        if action['get'] == 'item':
            buffer = '{ "Resultat" : "TROUVE" }' 
sys.stdout.buffer.write('Content-Type: application/json\r\n\r\n'.encode('utf-8'))
sys.stdout.buffer.write(buffer.encode('utf-8'))

