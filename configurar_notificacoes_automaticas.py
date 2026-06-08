#!/usr/bin/env python
import os
import django
from datetime import datetime, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from django.utils import timezone
from django.contrib.auth.models import User
from notificacoes.models import NotificacaoAgendada, TemplateNotificacao
from core.models import Inquilino

def mostrar_opcoes_automatizacao():
    """Mostra as opções de automatização disponíveis"""
    print("\n" + "="*60)
    print("🤖 SISTEMA DE NOTIFICAÇÕES AUTOMATIZADAS")
    print("="*60)
    
    print("\n📋 OPÇÕES DISPONÍVEIS:")
    print("\n1. ⏰ AGENDAMENTO ÚNICO")
    print("   - Enviar notificação em data/hora específica")
    print("   - Ideal para comunicados pontuais")
    
    print("\n2. 🔄 AGENDAMENTO RECORRENTE")
    print("   - Diário: Todos os dias")
    print("   - Semanal: Uma vez por semana")
    print("   - Mensal: Uma vez por mês")
    print("   - Anual: Uma vez por ano")
    
    print("\n3. 🎯 FILTROS AUTOMÁTICOS")
    print("   - Contratos próximos ao vencimento")
    print("   - Inquilinos com contratos ativos")
    print("   - Filtros personalizados por critérios")
    
    print("\n4. 📱 CANAIS DISPONÍVEIS")
    print("   - E-mail")
    print("   - WhatsApp")
    print("   - SMS (futuro)")

def verificar_agendamentos_ativos():
    """Verifica agendamentos ativos no sistema"""
    print("\n" + "="*60)
    print("📊 AGENDAMENTOS ATIVOS")
    print("="*60)
    
    agendamentos = NotificacaoAgendada.objects.filter(
        status__in=['AGENDADA', 'PROCESSANDO']
    ).order_by('data_envio')
    
    if not agendamentos:
        print("\n❌ Nenhum agendamento ativo encontrado.")
        return
    
    for agendamento in agendamentos:
        print(f"\n📌 {agendamento.nome_campanha}")
        print(f"   📅 Próximo envio: {agendamento.proximo_envio or agendamento.data_envio}")
        print(f"   🔄 Recorrência: {agendamento.get_recorrencia_display()}")
        print(f"   📊 Status: {agendamento.get_status_display()}")
        print(f"   👥 Destinatários: {agendamento.inquilinos.count() or 'Filtro automático'}")

def criar_agendamento_exemplo():
    """Cria um exemplo de agendamento automático"""
    print("\n" + "="*60)
    print("🛠️ CRIANDO AGENDAMENTO DE EXEMPLO")
    print("="*60)
    
    # Buscar template de vencimento
    template = TemplateNotificacao.objects.filter(
        tipo='VENCIMENTO',
        ativo=True
    ).first()
    
    if not template:
        print("\n❌ Nenhum template de vencimento encontrado.")
        print("   Crie um template primeiro no admin: /admin/notificacoes/templatenotificacao/")
        return
    
    # Buscar usuário admin
    usuario = User.objects.filter(is_superuser=True).first()
    if not usuario:
        print("\n❌ Nenhum usuário administrador encontrado.")
        return
    
    # Verificar se já existe
    nome_campanha = "Lembrete Automático - Vencimentos 7 dias"
    if NotificacaoAgendada.objects.filter(
        nome_campanha=nome_campanha,
        status__in=['AGENDADA', 'PROCESSANDO']
    ).exists():
        print(f"\n⚠️ Agendamento '{nome_campanha}' já existe.")
        return
    
    # Criar agendamento
    agendamento = NotificacaoAgendada.objects.create(
        template=template,
        nome_campanha=nome_campanha,
        descricao="Notificação automática para contratos com vencimento em 7 dias",
        data_envio=timezone.now() + timedelta(hours=1),  # Próxima hora
        recorrencia='DIARIA',  # Verificar diariamente
        intervalo_recorrencia=1,
        filtro_personalizado={
            'vencimento_proximo': 7,  # 7 dias
            'contratos_ativos': True,
            'canais': ['EMAIL', 'WHATSAPP']
        },
        prioridade='ALTA',
        usuario_criador=usuario
    )
    
    print(f"\n✅ Agendamento criado com sucesso!")
    print(f"   📌 Nome: {agendamento.nome_campanha}")
    print(f"   📅 Próximo envio: {agendamento.data_envio}")
    print(f"   🔄 Recorrência: {agendamento.get_recorrencia_display()}")
    print(f"   🎯 Filtro: Contratos vencendo em 7 dias")

def mostrar_comandos_uteis():
    """Mostra comandos úteis para gerenciar notificações"""
    print("\n" + "="*60)
    print("🔧 COMANDOS ÚTEIS")
    print("="*60)
    
    print("\n📋 GERENCIAMENTO:")
    print("\n1. Processar notificações agendadas:")
    print("   python manage.py processar_notificacoes")
    
    print("\n2. Criar agendamentos automáticos:")
    print("   python manage.py agendar_verificacoes --periodo diario --dias 7,15,30")
    
    print("\n3. Verificar vencimentos manualmente:")
    print("   python manage.py verificar_vencimentos --dias 7")
    
    print("\n4. Serviço contínuo de notificações:")
    print("   python manage.py servico_notificacoes")
    
    print("\n🌐 INTERFACE WEB:")
    print("\n1. Gerenciar agendamentos:")
    print("   http://localhost:8000/notificacoes/agendamentos/")
    
    print("\n2. Criar novos agendamentos:")
    print("   http://localhost:8000/notificacoes/agendar/")
    
    print("\n3. Enviar notificações:")
    print("   http://localhost:8000/notificacoes/enviar/")
    
    print("\n4. Admin (configurações avançadas):")
    print("   http://localhost:8000/admin/notificacoes/")

def mostrar_configuracao_completa():
    """Mostra como configurar um sistema completo"""
    print("\n" + "="*60)
    print("⚙️ CONFIGURAÇÃO COMPLETA")
    print("="*60)
    
    print("\n🎯 PARA AUTOMATIZAR COMPLETAMENTE:")
    
    print("\n1️⃣ CRIAR TEMPLATES (Admin):")
    print("   - Acesse: /admin/notificacoes/templatenotificacao/")
    print("   - Crie templates para: Vencimento, Cobrança, Lembretes")
    
    print("\n2️⃣ CONFIGURAR AGENDAMENTOS:")
    print("   - Vencimento 30 dias: Mensal")
    print("   - Vencimento 15 dias: Quinzenal")
    print("   - Vencimento 7 dias: Semanal")
    print("   - Vencimento 3 dias: Diário")
    
    print("\n3️⃣ ATIVAR SERVIÇO:")
    print("   - Execute: python manage.py servico_notificacoes")
    print("   - Mantenha rodando em background")
    
    print("\n4️⃣ MONITORAR:")
    print("   - Verifique logs regularmente")
    print("   - Acompanhe estatísticas de envio")
    print("   - Ajuste filtros conforme necessário")

if __name__ == '__main__':
    try:
        mostrar_opcoes_automatizacao()
        verificar_agendamentos_ativos()
        criar_agendamento_exemplo()
        mostrar_comandos_uteis()
        mostrar_configuracao_completa()
        
        print("\n" + "="*60)
        print("✅ CONFIGURAÇÃO CONCLUÍDA")
        print("="*60)
        print("\n💡 PRÓXIMOS PASSOS:")
        print("1. Acesse o admin para criar/editar templates")
        print("2. Configure agendamentos via interface web")
        print("3. Inicie o serviço de notificações")
        print("4. Monitore os envios nos logs")
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        print("\nVerifique se o Django está configurado corretamente.")
