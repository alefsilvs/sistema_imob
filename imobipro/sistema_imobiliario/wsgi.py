"""
WSGI config for sistema_imobiliario project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    if os.getenv('DATABASE_URL') or os.getenv('RAILWAY_ENVIRONMENT') or os.getenv('PORT'):
        os.environ['DJANGO_SETTINGS_MODULE'] = 'sistema_imobiliario.settings_railway'
    else:
        os.environ['DJANGO_SETTINGS_MODULE'] = 'sistema_imobiliario.settings'

should_auto_migrate = (
    os.environ.get('DJANGO_SETTINGS_MODULE') == 'sistema_imobiliario.settings_railway'
    or bool(os.getenv('DATABASE_URL'))
)

if should_auto_migrate and not os.getenv('DISABLE_AUTOMIGRATE'):
    try:
        import django
        django.setup()
        from django.core.management import call_command
        from django.db import connection

        def _postgres_table_exists(table_name: str) -> bool:
            with connection.cursor() as cursor:
                cursor.execute('SELECT to_regclass(%s);', [f'public.{table_name}'])
                return cursor.fetchone()[0] is not None

        needs_migrate = True
        if connection.vendor == 'postgresql':
            needs_migrate = not _postgres_table_exists('security_loginattempt') or not _postgres_table_exists('security_blockedip')

        if needs_migrate:
            if connection.vendor == 'postgresql':
                with connection.cursor() as cursor:
                    cursor.execute('SET search_path TO public;')
                    cursor.execute('SELECT pg_advisory_lock(%s);', [81723491])

            try:
                if connection.vendor != 'postgresql' or not _postgres_table_exists('security_loginattempt') or not _postgres_table_exists('security_blockedip'):
                    call_command('migrate', interactive=False, verbosity=1)

                if connection.vendor == 'postgresql' and (not _postgres_table_exists('security_loginattempt') or not _postgres_table_exists('security_blockedip')):
                    call_command('migrate', 'security', 'zero', fake=True, interactive=False, verbosity=1)
                    call_command('migrate', 'security', interactive=False, verbosity=1)
            finally:
                if connection.vendor == 'postgresql':
                    with connection.cursor() as cursor:
                        cursor.execute('SELECT pg_advisory_unlock(%s);', [81723491])
    except Exception:
        pass

application = get_wsgi_application()
