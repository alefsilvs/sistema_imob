from django.core.management.base import BaseCommand

from notificacoes.cobranca import processar_cobrancas_whatsapp
from saas.models import Tenant


class Command(BaseCommand):
    help = 'Envia cobranças automáticas via WhatsApp para aluguel/IPTU em atraso'

    def add_arguments(self, parser):
        parser.add_argument('--tenant-id', type=int, help='Executa apenas para um tenant específico')
        parser.add_argument('--dry-run', action='store_true', help='Simula envios sem mandar mensagens')
        parser.add_argument('--force', action='store_true', help='Força envio mesmo se já enviado no nível')
        parser.add_argument(
            '--tipo',
            type=str,
            choices=['ALUGUEL', 'IPTU_CONTRATO', 'IPTU_PARCELA'],
            help='Filtra somente um tipo de cobrança'
        )

    def handle(self, *args, **options):
        tenant_id = options.get('tenant_id')
        dry_run = options.get('dry_run', False)
        force = options.get('force', False)
        somente_tipo = options.get('tipo')

        tenants = Tenant.objects.filter(status__in=['ativo', 'trial'])
        if tenant_id:
            tenants = tenants.filter(id=tenant_id)

        if not tenants.exists():
            self.stdout.write(self.style.WARNING('Nenhum tenant encontrado para processar.'))
            return

        total_sent = 0
        total_errors = 0
        total_skipped = 0

        for tenant in tenants.order_by('id'):
            result = processar_cobrancas_whatsapp(
                tenant=tenant,
                dry_run=dry_run,
                force=force,
                somente_tipo=somente_tipo,
            )
            total_sent += result.get('enviadas', 0)
            total_errors += result.get('erros', 0)
            total_skipped += result.get('ignoradas', 0)

            self.stdout.write(
                f"Tenant {tenant.id} ({tenant.nome_empresa}): "
                f"enviadas={result.get('enviadas', 0)} "
                f"erros={result.get('erros', 0)} "
                f"ignoradas={result.get('ignoradas', 0)}"
            )

        self.stdout.write('')
        self.stdout.write('RESUMO:')
        self.stdout.write(f'- Enviadas: {total_sent}')
        self.stdout.write(f'- Erros: {total_errors}')
        self.stdout.write(f'- Ignoradas: {total_skipped}')
        if dry_run:
            self.stdout.write(self.style.WARNING('*** DRY-RUN: nenhum WhatsApp foi enviado ***'))

