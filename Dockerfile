FROM python:3.12-alpine
LABEL authors="marwanfazora"

# setup working directory
WORKDIR /home/user/fathaker/

# installing packages
COPY requirements.txt /home/user/fathaker
RUN pip install -r requirements.txt

# copy project files
COPY . /home/user/fathaker/

# collect statics
RUN python manage.py collectstatic --noinput

# setup NGINX
#RUN apt-get update && apt-get install -y nginx
RUN  apk update && apk add nginx

COPY deployment/nginx.conf /etc/nginx/sites-available/default

# setup Gunicorn
RUN pip install gunicorn
CMD gunicorn fathaker.wsgi:application --workers 3 --bind 0.0.0.0:8000

#CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

EXPOSE 8000