export LC_ALL=C.UTF-8
export LANG=C.UTF-8

cron

echo "04 * * * * /usr/local/bin/python3 /app/newminisab.py check" | crontab - -u minisab

sudo -u minisab python3 ./newminisab.py check

sudo -u minisab gunicorn -b :3000 --log-file /data/gunicorn.log flaskminisab:app