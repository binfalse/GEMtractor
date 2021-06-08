FROM python:3
ENV PYTHONUNBUFFERED 1

# install requirements
RUN mkdir /code
COPY requirements.txt /code
COPY src /code
RUN pip3 install -r /code/requirements.txt


WORKDIR /code

RUN python3 manage.py migrate

# start gunicorn to serve the python stuff
CMD gunicorn --timeout 600 --bind 0.0.0.0:80 gemtractor.wsgi:application
