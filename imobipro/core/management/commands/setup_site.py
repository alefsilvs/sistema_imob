from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from django.conf import settings


class Command(BaseCommand):
    help = 'Configura o site com o domínio correto para emails de recuperação de senha'

    def handle(self, *args, **options):
        try:
            # Obter ou criar o site padrão
            site, created = Site.objects.get_or_create(
                id=settings.SITE_ID,
                defaults={
                    'domain': '127.0.0.1:8000',
                    'name': 'ImobiPro - Sistema Imobiliário'
                }
            )
            
            if not created:
                # Atualizar site existente
                site.domain = '127.0.0.1:8000'
                site.name = 'ImobiPro - Sistema Imobiliário'
                site.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Site atualizado: {site.domain} - {site.name}'
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Site criado: {site.domain} - {site.name}'
                    )
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Erro ao configurar site: {str(e)}')
            )