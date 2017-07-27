export LC_ALL=C.UTF-8
export LANG=C.UTF-8

python3 ./newminisab.py check

gunicorn -b :3000 --log-file /data/gunicorn.log flaskminisab:app