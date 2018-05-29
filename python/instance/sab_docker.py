import os

MINISAB_SAB_CNX = True
MINISAB_SAB_HOST = 'sabnzbd'
MINISAB_SAB_PORT = int(os.environ['SABNZBD_PORT']) if os.environ['SABNZBD_PORT'] != '' else 8080
MINISAB_SAB_CLE = 'a completer'
