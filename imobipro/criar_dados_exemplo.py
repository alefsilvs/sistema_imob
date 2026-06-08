#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import django
from datetime import date, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from core.models import Inquilino, Proprietario
from imoveis.models import Imovel
from contratos.models import Contrato
from decimal import Decimal

def criar_dados_exemplo():
    print("Criando dados de exemplo...")
    
    # Criar proprietários
    proprietario1, created = Proprietario.objects.get_or_create(
        cpf_cnpj='12345678901',
        defaults={
            'nome': 'João Silva Santos',
            'email': 'joao.silva@email.com',
            'telefone': '(11) 99999-1111',
            'endereco': 'Rua dos Proprietários, 100',
            'cidade': 'São Paulo',
            'estado': 'SP',
            'cep': '01234-567',
            'tipo': 'PF'
        }
    )
    
    proprietario2, created = Proprietario.objects.get_or_create(
        cpf_cnpj='98765432109',
        defaults={
            'nome': 'Maria Oliveira Costa',
            'email': 'maria.oliveira@email.com',
            'telefone': '(11) 99999-2222',
            'endereco': 'Av. Central, 500',
            'cidade': 'São Paulo',
            'estado': 'SP',
            'cep': '04567-890',
            'tipo': 'PF'
        }
    )
    
    # Criar inquilinos
    inquilino1, created = Inquilino.objects.get_or_create(
        cpf_cnpj='11122233344',
        defaults={
            'nome': 'Carlos Eduardo Mendes',
            'email': 'carlos.mendes@email.com',
            'telefone': '(11) 98888-1111',
            'endereco': 'Rua Temporária, 50',
            'cidade': 'São Paulo',
            'estado': 'SP',
            'cep': '02345-678',
            'profissao': 'Engenheiro',
            'renda': Decimal('8500.00'),
            'tipo': 'PF'
        }
    )
    
    inquilino2, created = Inquilino.objects.get_or_create(
        cpf_cnpj='55566677788',
        defaults={
            'nome': 'Ana Paula Rodrigues',
            'email': 'ana.rodrigues@email.com',
            'telefone': '(11) 98888-2222',
            'endereco': 'Rua dos Inquilinos, 200',
            'cidade': 'São Paulo',
            'estado': 'SP',
            'cep': '03456-789',
            'profissao': 'Advogada',
            'renda': Decimal('12000.00'),
            'tipo': 'PF'
        }
    )
    
    inquilino3, created = Inquilino.objects.get_or_create(
        cpf_cnpj='99988877766',
        defaults={
            'nome': 'Roberto Santos Lima',
            'email': 'roberto.lima@email.com',
            'telefone': '(11) 98888-3333',
            'endereco': 'Av. Paulista, 1000',
            'cidade': 'São Paulo',
            'estado': 'SP',
            'cep': '01310-100',
            'profissao': 'Médico',
            'renda': Decimal('15000.00'),
            'tipo': 'PF'
        }
    )
    
    # Criar imóveis
    imovel1, created = Imovel.objects.get_or_create(
        codigo='APT301',
        defaults={
            'descricao': 'Apartamento 301 - Edifício Central Plaza',
            'tipo': 'APARTAMENTO',
            'endereco': 'Rua das Flores, 123',
            'bairro': 'Centro',
            'cidade': 'São Paulo',
            'estado': 'SP',
            'cep': '01234-567',
            'area_total': Decimal('85.50'),
            'quartos': 3,
            'banheiros': 2,
            'vagas_garagem': 1,
            'valor_aluguel': Decimal('2800.00'),
            'valor_condominio': Decimal('450.00'),
            'valor_iptu': Decimal('180.00'),
            'proprietario': proprietario1,
            'status': 'OCUPADO'
        }
    )
    
    imovel2, created = Imovel.objects.get_or_create(
        codigo='CASA456',
        defaults={
            'descricao': 'Casa Jardim América',
            'tipo': 'CASA',
            'endereco': 'Rua Paraíba, 456',
            'bairro': 'Jardim América',
            'cidade': 'São Paulo',
            'estado': 'SP',
            'cep': '01234-890',
            'area_total': Decimal('150.00'),
            'quartos': 4,
            'banheiros': 3,
            'vagas_garagem': 2,
            'valor_aluguel': Decimal('4500.00'),
            'valor_condominio': Decimal('0.00'),
            'valor_iptu': Decimal('320.00'),
            'proprietario': proprietario2,
            'status': 'OCUPADO'
        }
    )
    
    imovel3, created = Imovel.objects.get_or_create(
        codigo='SALA205',
        defaults={
            'descricao': 'Sala Comercial 205 - Torre Business',
            'tipo': 'COMERCIAL',
            'endereco': 'Rua Augusta, 789',
            'bairro': 'Consolação',
            'cidade': 'São Paulo',
            'estado': 'SP',
            'cep': '01305-100',
            'area_total': Decimal('45.00'),
            'quartos': 0,
            'banheiros': 1,
            'vagas_garagem': 1,
            'valor_aluguel': Decimal('1800.00'),
            'valor_condominio': Decimal('280.00'),
            'valor_iptu': Decimal('120.00'),
            'proprietario': proprietario1,
            'status': 'OCUPADO'
        }
    )
    
    # Criar contratos próximos ao vencimento
    hoje = date.today()
    
    # Contrato vencendo em 10 dias (urgente)
    contrato1, created = Contrato.objects.get_or_create(
        numero='CONT-2024-001',
        defaults={
            'imovel': imovel1,
            'inquilino': inquilino1,
            'data_inicio': hoje - timedelta(days=355),  # Contrato de 1 ano, faltam 10 dias
            'data_fim': hoje + timedelta(days=10),
            'valor_aluguel': imovel1.valor_aluguel,
            'valor_condominio': imovel1.valor_condominio,
            'valor_iptu': imovel1.valor_iptu,
            'dia_vencimento': 5,
            'status': 'ATIVO',
            'observacoes': 'Contrato próximo ao vencimento - renovação necessária'
        }
    )
    
    # Contrato vencendo em 25 dias
    contrato2, created = Contrato.objects.get_or_create(
        numero='CONT-2024-002',
        defaults={
            'imovel': imovel2,
            'inquilino': inquilino2,
            'data_inicio': hoje - timedelta(days=340),  # Contrato de 1 ano, faltam 25 dias
            'data_fim': hoje + timedelta(days=25),
            'valor_aluguel': imovel2.valor_aluguel,
            'valor_condominio': imovel2.valor_condominio,
            'valor_iptu': imovel2.valor_iptu,
            'dia_vencimento': 10,
            'status': 'ATIVO',
            'observacoes': 'Inquilino interessado em renovação'
        }
    )
    
    # Contrato vencendo em 28 dias
    contrato3, created = Contrato.objects.get_or_create(
        numero='CONT-2024-003',
        defaults={
            'imovel': imovel3,
            'inquilino': inquilino3,
            'data_inicio': hoje - timedelta(days=337),  # Contrato de 1 ano, faltam 28 dias
            'data_fim': hoje + timedelta(days=28),
            'valor_aluguel': imovel3.valor_aluguel,
            'valor_condominio': imovel3.valor_condominio,
            'valor_iptu': imovel3.valor_iptu,
            'dia_vencimento': 15,
            'status': 'ATIVO',
            'observacoes': 'Aguardando definição sobre renovação'
        }
    )
    
    print("✅ Dados de exemplo criados com sucesso!")
    print(f"📊 Proprietários: {Proprietario.objects.count()}")
    print(f"🏠 Imóveis: {Imovel.objects.count()}")
    print(f"👥 Inquilinos: {Inquilino.objects.count()}")
    print(f"📋 Contratos: {Contrato.objects.count()}")
    print(f"⚠️  Contratos vencendo em 30 dias: {Contrato.objects.filter(data_fim__lte=hoje + timedelta(days=30), status='ATIVO').count()}")

if __name__ == '__main__':
    criar_dados_exemplo()