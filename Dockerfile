FROM python:3.12-slim

WORKDIR /fathaker
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Static assets only: no database, bucket, or runtime secrets.
RUN DEBLOYED=0 DEBUG=0 SQLITE_PATH=:memory: python manage.py collectstatic --noinput

EXPOSE 8080
ENTRYPOINT ["sh", "/fathaker/deployment/entrypoint.sh"]
