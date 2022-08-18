FROM python:3.7.10-slim

COPY requirements.txt .
RUN apt-get update
RUN apt-get install -y libpq-dev python-dev gcc
RUN pip install -r requirements.txt

COPY . .
ENTRYPOINT [ "python" ]
