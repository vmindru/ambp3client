FROM python:3.7-alpine

RUN apk add gcc musl-dev mariadb-dev

RUN pip install --upgrade pip

WORKDIR /code
COPY requirements.txt .
RUN pip install -r ./requirements.txt