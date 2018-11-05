FROM python:3.6

RUN mkdir -p /u/app/service/instance

ADD . /u/app/service/

WORKDIR /u/app/service/

RUN pip install pipenv && \
  pipenv install --system

CMD uwsgi --http-socket 0.0.0.0:5000 --wsgi-file run.py --callable app
