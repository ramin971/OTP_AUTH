FROM python:3.11-alpine

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN addgroup app && adduser -S -G app app

WORKDIR /home/app/web

RUN pip install --upgrade pip

RUN apk update \
    && apk add postgresql-dev gcc python3-dev musl-dev linux-headers

COPY ./requirements.txt .
RUN pip install -r requirements.txt
RUN  pip install psycopg2 && pip install gunicorn


#media files
# RUN mkdir /home/app/web/media
RUN mkdir /home/app/web/static
# RUN chown -R app:app ./media
RUN chown -R app:app ./static
# copy entrypoint.sh
COPY ./entrypoint.sh .
RUN sed -i 's/\r$//g' /home/app/web/entrypoint.sh
RUN chown -R app:app /home/app/web/entrypoint.sh
RUN chmod +x /home/app/web/entrypoint.sh


COPY . .

RUN chown -R app:app /home/app/web
USER app

ENTRYPOINT ["/home/app/web/entrypoint.sh"]