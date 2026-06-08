from django.core.management.base import BaseCommand
from django.db.models import Q

from notificacoes.models import TemplateNotificacao, TipoNotificacao


class Command(BaseCommand):
    help = 'Desativa templates/notificações legadas de banca/feira'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Mostra o que seria desativado sem alterar')

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)

        filtro = Q(nome__icontains='banca') | Q(nome__icontains='feira')
        templates = TemplateNotificacao.objects.filter(filtro, ativo=True)
        tipos = TipoNotificacao.objects.filter(Q(nome__icontains='banca') | Q(nome__icontains='feira'), ativo=True)

        self.stdout.write(f'Templates encontrados: {templates.count()}')
        for t in templates.order_by('id'):
            self.stdout.write(f'- Template {t.id}: {t.nome}')
        self.stdout.write(f'Tipos legados encontrados: {tipos.count()}')
        for x in tipos.order_by('id'):
            self.stdout.write(f'- Tipo {x.id}: {x.nome}')

        if dry_run:
            self.stdout.write(self.style.WARNING('*** DRY-RUN: nada foi alterado ***'))
            return

        templates.update(ativo=False)
        tipos.update(ativo=False)
        self.stdout.write(self.style.SUCCESS('Templates e tipos de feira/banca desativados.'))

