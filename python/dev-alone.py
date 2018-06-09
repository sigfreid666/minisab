from minisab import create_app
import os

os.environ['MINISAB_AUTRE_DBFILE'] = "./minisab.db"
os.environ['MINISAB_AUTRE_DUMPDIR'] = "./temp"
os.environ['MINISABINV_CONFIG_FILE'] = "/temp/config.json"
os.environ['MINISABINV_AUTRE_CONFIG'] = "redis_docker.py"
os.environ['MINISABINV_URL_EXTERNE'] = "http://localhost:9100/"

app = create_app('dev')
