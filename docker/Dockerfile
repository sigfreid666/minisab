FROM python:3.5

#RUN apt-get update \
#    && apt-get install -y python3 python3-pip python3-requests

RUN apt-get update \
    && apt-get install -y cron sudo supervisor

RUN pip3 install requests peewee flask gunicorn redis

ENV DB_FILE="/data/minisab.db" LOG_FILE="/data/minisab.log" REDIS_IP="192.168.0.8" REDIS_PORT="9020" SAB_IP="192.168.0.8" SAB_CLE_API="6f8af3c4c4487edf93d96979ed7d2321"

RUN export LC_ALL=C.UTF-8 LANG=C.UTF-8

RUN groupadd -r minisab && useradd --no-log-init -r -g minisab minisab
RUN mkdir /app

RUN mkdir /data

WORKDIR /app

ADD src.tar .

ADD supervisor.conf /app

ADD cronfile /app

# USER minisab:minisab

RUN echo "dbfile = '${DB_FILE}'" > /app/settings_local.py; \
    echo "logfile = '${LOG_FILE}'" >> /app/settings_local.py; \
    echo "host_redis = '${REDIS_IP}'" >> /app/settings_local.py; \
    echo "port_redis = ${REDIS_PORT}" >> /app/settings_local.py; \
    echo "host_sabG = '${SAB_IP}'" >> /app/settings_local.py; \
    echo "sabnzbd_nc_cle_api = '${SAB_CLE_API}'" >> /app/settings_local.py

#RUN export LC_ALL=C.UTF-8 && export LANG=C.UTF-8 && python3 ./newminisab.py check

RUN chown -R minisab:minisab /data;\
    chown -R minisab:minisab /app;

RUN cat /app/cronfile | crontab - -u minisab

RUN crontab -l -u minisab

VOLUME /data

EXPOSE 3000

CMD supervisord -c /app/supervisor.conf -n