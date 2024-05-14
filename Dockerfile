FROM python:3.12-alpine
LABEL authors="marwanfazora"

# setup working directory
WORKDIR /fathaker/

# installing packages
COPY requirements.txt /fathaker/requirements.txt
RUN pip install -r requirements.txt && pip install gunicorn

# copy project files
COPY . /fathaker/

#setup environment variables
ENV PYTHONUNBUFFERED=1
COPY deployment/.env /fathaker/fathaker/.env

COPY ./deployment/entrypoint.sh /
ENTRYPOINT ["sh", "/entrypoint.sh"]

## collect statics
#RUN python manage.py collectstatic --noinput
#
## setup Gunicorn
#RUN pip install gunicorn
#CMD gunicorn fathaker.wsgi:application --workers 3 --bind 0.0.0.0:8000
#
#EXPOSE 8000