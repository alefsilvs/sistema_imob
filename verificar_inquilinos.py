import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_imobiliario.settings')
django.setup()

from core.models import Inquilino
from notificacoes.models import TemplateNotificacao

def verificar_inquilinos():
    print("🔍 Verificando inquilinos cadastrados no sistema")
    print("="*50)
    
    # Verificar total de inquilinos
    total_inquilinos = Inquilino.objects.count()
    print(f"📊 Total de inquilinos: {total_inquilinos}")
    
    if total_inquilinos == 0:
        print("❌ Nenhum inquilino cadastrado no sistema!")
        print("\n💡 Para testar o WhatsApp, você precisa:")
        print("   1. Cadastrar pelo menos um inquilino")
        print("   2. Adicionar um telefone válido ao inquilino")
        print("   3. Criar um template de notificação")
        return
    
    # Verificar inquilinos ativos
    inquilinos_ativos = Inquilino.objects.filter(ativo=True)
    print(f"✅ Inquilinos ativos: {inquilinos_ativos.count()}")
    
    # Verificar inquilinos com telefone
    com_telefone = Inquilino.objects.filter(
        ativo=True,
        telefone__isnull=False
    ).exclude(telefone__exact='')
    print(f"📱 Inquilinos com telefone: {com_telefone.count()}")
    
    # Listar inquilinos com telefone
    if com_telefone.exists():
        print("\n📋 Inquilinos disponíveis para WhatsApp:")
        for inquilino in com_telefone[:5]:  # Mostrar apenas os primeiros 5
            print(f"   • {inquilino.nome} - {inquilino.telefone}")
        
        if com_telefone.count() > 5:
            print(f"   ... e mais {com_telefone.count() - 5} inquilinos")
    else:
        print("❌ Nenhum inquilino tem telefone cadastrado!")
        print("\n💡 Para enviar WhatsApp, adicione telefones aos inquilinos")
        print("   Formato recomendado: +5561999999999 (com código do país)")
    
    # Verificar templates disponíveis
    templates = TemplateNotificacao.objects.filter(ativo=True)
    print(f"\n📝 Templates disponíveis: {templates.count()}")
    
    if templates.exists():
        print("\n📋 Templates ativos:")
        for template in templates[:3]:
            print(f"   • {template.nome} ({template.tipo})")
    else:
        print("❌ Nenhum template ativo encontrado!")
        print("\n💡 Crie pelo menos um template para enviar notificações")
    
    print("\n" + "="*50)
    
    if com_telefone.exists() and templates.exists():
        print("✅ Sistema pronto para enviar notificações WhatsApp!")
        print("\n🚀 Próximos passos:")
        print("   1. Acesse a página de notificações")
        print("   2. Selecione um template")
        print("   3. Escolha 'WhatsApp' como canal")
        print("   4. Selecione os inquilinos com telefone")
        print("   5. Clique em 'Enviar Notificações'")
    else:
        print("⚠️  Sistema não está pronto para WhatsApp")
        print("\n📝 Checklist:")
        print(f"   {'✅' if total_inquilinos > 0 else '❌'} Inquilinos cadastrados")
        print(f"   {'✅' if com_telefone.exists() else '❌'} Telefones cadastrados")
        print(f"   {'✅' if templates.exists() else '❌'} Templates ativos")

if __name__ == '__main__':
    verificar_inquilinos()