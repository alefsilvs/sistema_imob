FROM python:3.11.9-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

WORKDIR /app

RUN groupadd -r sistema_imo && useradd -r -g sistema_imo -d /home/sistema_imo -m sistema_imo

COPY requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip && python -m pip install -r /app/requirements.txt

COPY . /app

WORKDIR /app/imobipro

ENV DJANGO_SETTINGS_MODULE=sistema_imobiliario.settings_railway
ENV DEBUG=False

EXPOSE 8000

CMD ["bash", "-lc", "export PORT=${PORT:-8000}; export GUNICORN_USER=; export GUNICORN_GROUP=; export GUNICORN_PIDFILE=; export GUNICORN_CMD_ARGS=; for i in 1 2 3 4 5; do python manage.py migrate --noinput --run-syncdb && break || (echo \"migrate falhou (tentativa $i/5), aguardando...\" && sleep 3); done; if [ \"${BOOTSTRAP_SUPERUSER}\" = \"1\" ] && [ -n \"${DJANGO_SUPERUSER_USERNAME}\" ] && [ -n \"${DJANGO_SUPERUSER_PASSWORD}\" ]; then python manage.py shell -c \"import os; from django.contrib.auth import get_user_model; User=get_user_model(); u=os.environ.get('DJANGO_SUPERUSER_USERNAME'); p=os.environ.get('DJANGO_SUPERUSER_PASSWORD'); e=os.environ.get('DJANGO_SUPERUSER_EMAIL',''); obj,created=User.objects.get_or_create(username=u, defaults={'email': e, 'is_staff': True, 'is_superuser': True, 'is_active': True}); obj.is_staff=True; obj.is_superuser=True; obj.is_active=True; obj.email = e or obj.email; obj.set_password(p); obj.save(); print('bootstrap_superuser', u, 'created' if created else 'updated')\"; fi; python manage.py collectstatic --noinput --clear; exec gunicorn sistema_imobiliario.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120 --access-logfile - --error-logfile - --pid /tmp/gunicorn.pid --worker-tmp-dir /tmp"]
