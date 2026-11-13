#!/bin/sh

set -eu

if [ "$#" -gt 0 ]; then
    exec "$@"
fi

exec gunicorn fathaker.wsgi:application \
    --workers 1 --threads 4 \
    --bind "0.0.0.0:${PORT:-8080}" \
    --access-logfile - --error-logfile -
