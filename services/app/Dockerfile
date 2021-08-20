FROM python:3.9-slim

WORKDIR /app

EXPOSE 8000 8001

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    mkvtoolnix

COPY services/app/requirements.txt /conf/
RUN pip install -r /conf/requirements.txt

COPY services/app/uwsgi.ini services/app/mime.types /conf/
COPY services/app/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod a+x /usr/local/bin/entrypoint.sh
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

COPY app ./

CMD ["uwsgi"]
