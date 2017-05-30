import logging

# dbfile = 'minisab.db'
# logfile = 'minisab.log'

try:
        from settings_local import *
except ImportError:
        logging.error('Impossible d''importer le settings local')
        pass
