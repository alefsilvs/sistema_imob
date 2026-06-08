from django.core.management.base import BaseCommand
from django.db.models import Q

from core.models import Inquilino


class Command(BaseCommand):
    help = 'Remove inquilinos fictícios/dados de teste (mantém somente cadastrados reais)'

    def add_arguments(self, parser):
        parser.add_argument('--tenant-id', type=int, help='Limpa somente um tenant específico')
        parser.add_argument('--confirm', action='store_true', help='Confirma a exclusão (sem isso, apenas simula)')

    def handle(self, *args, **options):
        tenant_id = options.get('tenant_id')
        confirm = options.get('confirm', False)

        qs = Inquilino.objects.all()
        if tenant_id:
            qs = qs.filter(tenant_id=tenant_id)

        filtro = (
            Q(email__iendswith='@example.com') |
            Q(email__icontains='@test.') |
            Q(email__icontains='@teste.') |
            Q(email__icontains='@debug.') |
            Q(email__icontains='@save.') |
            Q(nome__icontains='teste') |
            Q(nome__icontains='debug') |
            Q(nome__icontains='inquilino ') |
            Q(cpf_cnpj__icontains='11144477735') |
            Q(cpf_cnpj__icontains='52998224725') |
            Q(cpf_cnpj__icontains='22233344487') |
            Q(cpf_cnpj__icontains='11122233344') |
            Q(cpf_cnpj__icontains='55566677788') |
            Q(cpf_cnpj__icontains='99988877766')
        )

        candidatos = qs.filter(filtro).order_by('id')
        total = candidatos.count()

        self.stdout.write(f'Inquilinos candidatos à remoção: {total}')
        for i in candidatos[:200]:
            self.stdout.write(f'- {i.id}: {i.nome} | {i.cpf_cnpj} | {i.email} | tenant={i.tenant_id}')
        if total > 200:
            self.stdout.write(f'... +{total - 200} (listagem limitada a 200)')

        if not confirm:
            self.stdout.write(self.style.WARNING('*** SIMULAÇÃO: nada foi removido (use --confirm) ***'))
            return

        deleted_count, _ = candidatos.delete()
        self.stdout.write(self.style.SUCCESS(f'Removidos {deleted_count} registros.'))

