from django.core.management.base import BaseCommand
from documentos.models import TipoDocumento, CategoriaDocumento
from saas.models import Tenant

class Command(BaseCommand):
    help = 'Cria tipos de documento básicos no sistema'

    def handle(self, *args, **options):
        # Pegar o primeiro tenant
        tenant = Tenant.objects.first()
        if not tenant:
            self.stdout.write(self.style.ERROR('Nenhum tenant encontrado!'))
            return
        
        self.stdout.write(f'Tenant encontrado: {tenant}')

        # Criar categorias básicas
        categorias = [
            {'nome': 'Contratos', 'descricao': 'Documentos contratuais'},
            {'nome': 'Financeiro', 'descricao': 'Documentos financeiros'},
            {'nome': 'Jurídico', 'descricao': 'Documentos jurídicos'},
            {'nome': 'Pessoal', 'descricao': 'Documentos pessoais'},
            {'nome': 'Imóveis', 'descricao': 'Documentos de imóveis'}
        ]

        for cat_data in categorias:
            categoria, created = CategoriaDocumento.objects.get_or_create(
                nome=cat_data['nome'],
                tenant=tenant,
                defaults={'descricao': cat_data['descricao']}
            )
            status = 'Criada' if created else 'Já existe'
            self.stdout.write(f'Categoria: {categoria.nome} - {status}')

        # Criar tipos de documento básicos
        tipos = [
            {'nome': 'Contrato de Locação', 'categoria': 'CONTRATOS'},
            {'nome': 'RG', 'categoria': 'PESSOAL'},
            {'nome': 'CPF', 'categoria': 'PESSOAL'},
            {'nome': 'Comprovante de Renda', 'categoria': 'FINANCEIRO'},
            {'nome': 'Comprovante de Residência', 'categoria': 'PESSOAL'},
            {'nome': 'IPTU', 'categoria': 'FINANCEIRO'},
            {'nome': 'Escritura', 'categoria': 'JURIDICO'},
            {'nome': 'Matrícula do Imóvel', 'categoria': 'JURIDICO'},
            {'nome': 'Laudo de Vistoria', 'categoria': 'IMOVEIS'},
            {'nome': 'Fotos do Imóvel', 'categoria': 'IMOVEIS'}
        ]

        for tipo_data in tipos:
            tipo, created = TipoDocumento.objects.get_or_create(
                nome=tipo_data['nome'],
                tenant=tenant,
                defaults={
                    'categoria': tipo_data['categoria'],
                    'descricao': f'Documento do tipo {tipo_data["nome"]}',
                    'ativo': True
                }
            )
            status = 'Criado' if created else 'Já existe'
            self.stdout.write(f'Tipo: {tipo.nome} - {status}')

        total_tipos = TipoDocumento.objects.filter(tenant=tenant).count()
        self.stdout.write(
            self.style.SUCCESS(f'Total de tipos no sistema: {total_tipos}')
        )