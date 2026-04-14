web: gunicorn herald_backend.wsgi:application --worker-class gthread --workers ${WEB_CONCURRENCY:-2} --threads ${GUNICORN_THREADS:-4} --timeout 120 --keep-alive 5
