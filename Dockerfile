FROM python:3
ENV PYTHONUNBUFFERED 1
RUN mkdir /code
WORKDIR /code
COPY requirements.txt /code
RUN pip3 install -r /code/requirements.txt
VOLUME /code
CMD gunicorn --timeout 600 --bind 0.0.0.0:80 enalyzer.wsgi:application
