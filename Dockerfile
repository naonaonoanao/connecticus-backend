FROM python:3.10-slim

ENV PYTHONPATH /app
ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY . .

WORKDIR /app

CMD [ "python3", "app/main.py" ]
