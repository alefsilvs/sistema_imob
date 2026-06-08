from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from contratos.models import Contrato
from core.models import Inquilino, Proprietario
from financeiro.models import Parcela
from imoveis.models import Imovel
from notificacoes.cobranca import _format_brl, _pick_level, processar_cobrancas_whatsapp
from notificacoes.models import CobrancaAutomaticaLog
from saas.models import PlanoComercial, Tenant


class CobrancaWhatsAppTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='admin_test', password='x', is_superuser=True)
        self.plano = PlanoComercial.objects.create(nome='Trial', tipo='trial', preco_mensal=0, is_trial=True)
        self.tenant = Tenant.objects.create(
            nome_empresa='Empresa Teste',
            slug='empresa-teste',
            subdominio='empresa-teste',
            usuario_admin=self.user,
            plano=self.plano,
            status='ativo',
            configuracoes={'cobranca_whatsapp': {'ativo': True, 'dias': [1, 5]}},
        )
        self.proprietario = Proprietario.objects.create(
            tenant=self.tenant,
            nome='Prop',
            tipo='PF',
            cpf_cnpj='11144477735',
            rg_ie='1',
            telefone='11999999999',
            email='p@example.com',
            endereco='Rua X',
            cep='00000-000',
            cidade='Cidade',
            estado='SP',
        )
        self.inquilino = Inquilino.objects.create(
            tenant=self.tenant,
            nome='Inq',
            tipo='PF',
            cpf_cnpj='52998224725',
            rg_ie='2',
            telefone='11988887777',
            email='i@example.com',
            endereco='Rua Y',
            cep='00000-000',
            cidade='Cidade',
            estado='SP',
        )
        self.imovel = Imovel.objects.create(
            tenant=self.tenant,
            codigo='IMVTEST',
            proprietario=self.proprietario,
            tipo='CASA',
            finalidade='RESIDENCIAL',
            endereco='Av Teste',
            numero='10',
            complemento='',
            bairro='Centro',
            cidade='Cidade',
            estado='SP',
            cep='00000-000',
            valor_aluguel=1000,
            valor_condominio=0,
            valor_iptu=0,
            valor_seguro=0,
        )
        hoje = timezone.now().date()
        self.contrato = Contrato.objects.create(
            tenant=self.tenant,
            numero='CTRTEST',
            imovel=self.imovel,
            inquilino=self.inquilino,
            data_inicio=hoje - timedelta(days=30),
            data_fim=hoje + timedelta(days=365),
            valor_aluguel=1000,
            valor_condominio=0,
            valor_iptu=0,
            dia_vencimento=10,
            tipo_reajuste='IPCA',
        )
        self.parcela = Parcela.objects.create(
            contrato=self.contrato,
            numero_parcela=1,
            data_vencimento=hoje - timedelta(days=6),
            valor_aluguel=1000,
            status='PENDENTE',
            tipo='ALUGUEL',
        )

    def test_format_brl(self):
        self.assertEqual(_format_brl(10), '10,00')
        self.assertEqual(_format_brl(1000.5), '1.000,50')

    def test_pick_level(self):
        nivel = _pick_level(6, [1, 5], self.tenant, 'ALUGUEL', parcela_id=self.parcela.id)
        self.assertEqual(nivel, 2)
        CobrancaAutomaticaLog.objects.create(
            tenant=self.tenant,
            inquilino=self.inquilino,
            contrato=self.contrato,
            parcela=self.parcela,
            tipo='ALUGUEL',
            nivel=2,
            canal='WHATSAPP',
            destinatario=self.inquilino.telefone,
            status='ENVIADA',
        )
        nivel2 = _pick_level(6, [1, 5], self.tenant, 'ALUGUEL', parcela_id=self.parcela.id)
        self.assertIsNone(nivel2)

    def test_dry_run_does_not_create_log(self):
        result = processar_cobrancas_whatsapp(tenant=self.tenant, dry_run=True)
        self.assertGreaterEqual(result.get('enviadas', 0), 1)
        self.assertEqual(CobrancaAutomaticaLog.objects.count(), 0)
