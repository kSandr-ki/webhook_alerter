FROM python:3

ENV TG_BOT_TOKEN='' \
    TG_CHAT_ID=''

COPY requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt

WORKDIR /app
COPY . .

EXPOSE 5000

CMD python webhook.py
