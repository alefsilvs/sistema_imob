#!/usr/bin/env python3
"""
Script de Configuração para Hospedagem Gratuita
Sistema Imobiliário - Configuração automática para Railway, Render e outras plataformas
"""

import os
import sys
import subprocess
import json
from pathlib import Path

class HospedagemGratuitaSetup:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.platforms = {
            'railway': {
                'name': 'Railway',
                'url': 'https://railway.app',
                'free_hours': 500,
                'ram': '1GB',
                'database': 'PostgreSQL incluído',
                'files': ['railway.json', 'Procfile', 'runtime.txt', '.env.railway.example']
            },
            'render': {
                'name': 'Render.com',
                'url': 'https://render.com',
                'free_hours': 750,
                'ram': '512MB',
                'database': 'PostgreSQL incluído',
                'files': ['render.yaml', 'build.sh', '.env.render.example']
            },
            'heroku': {
                'name': 'Heroku',
                'url': 'https://heroku.com',
                'free_hours': 0,
                'ram': 'Pago ($5+/mês)',
                'database': 'PostgreSQL pago',
                'files': ['Procfile', 'runtime.txt', '.env.heroku.example']
            }
        }

    def print_banner(self):
        """Exibe banner do script"""
        print("=" * 60)
        print("🚀 CONFIGURAÇÃO DE HOSPEDAGEM GRATUITA")
        print("Sistema Imobiliário - Deploy Automático")
        print("=" * 60)
        print()

    def check_requirements(self):
        """Verifica se os requisitos estão instalados"""
        print("🔍 Verificando requisitos...")
        
        requirements = {
            'git': 'git --version',
            'python': 'python --version',
            'pip': 'pip --version'
        }
        
        missing = []
        for req, cmd in requirements.items():
            try:
                subprocess.run(cmd.split(), capture_output=True, check=True)
                print(f"  ✅ {req} instalado")
            except (subprocess.CalledProcessError, FileNotFoundError):
                print(f"  ❌ {req} não encontrado")
                missing.append(req)
        
        if missing:
            print(f"\n⚠️  Instale os requisitos faltantes: {', '.join(missing)}")
            return False
        
        print("✅ Todos os requisitos atendidos!")
        return True

    def show_platforms(self):
        """Exibe informações das plataformas disponíveis"""
        print("\n📊 PLATAFORMAS DE HOSPEDAGEM GRATUITA DISPONÍVEIS:")
        print("-" * 60)
        
        for key, platform in self.platforms.items():
            status = "🟢 RECOMENDADO" if platform['free_hours'] > 0 else "🔴 PAGO"
            print(f"\n{platform['name']} ({key}) - {status}")
            print(f"  🌐 URL: {platform['url']}")
            print(f"  ⏰ Horas gratuitas: {platform['free_hours']}/mês")
            print(f"  💾 RAM: {platform['ram']}")
            print(f"  🗄️  Database: {platform['database']}")
            print(f"  📁 Arquivos: {', '.join(platform['files'])}")

    def select_platform(self):
        """Permite ao usuário selecionar uma plataforma"""
        print("\n🎯 SELEÇÃO DE PLATAFORMA:")
        print("1. Railway (Recomendado - 500h gratuitas)")
        print("2. Render.com (750h gratuitas)")
        print("3. Heroku (Pago - apenas referência)")
        print("4. Configurar todas")
        print("0. Sair")
        
        while True:
            try:
                choice = input("\nEscolha uma opção (0-4): ").strip()
                
                if choice == "0":
                    print("👋 Saindo...")
                    sys.exit(0)
                elif choice == "1":
                    return ['railway']
                elif choice == "2":
                    return ['render']
                elif choice == "3":
                    return ['heroku']
                elif choice == "4":
                    return list(self.platforms.keys())
                else:
                    print("❌ Opção inválida. Tente novamente.")
            except KeyboardInterrupt:
                print("\n👋 Saindo...")
                sys.exit(0)

    def check_files_exist(self, platform):
        """Verifica se os arquivos da plataforma existem"""
        print(f"\n🔍 Verificando arquivos para {self.platforms[platform]['name']}...")
        
        files_status = {}
        for file in self.platforms[platform]['files']:
            file_path = self.base_dir / file
            exists = file_path.exists()
            files_status[file] = exists
            status = "✅" if exists else "❌"
            print(f"  {status} {file}")
        
        return files_status

    def create_env_file(self, platform):
        """Cria arquivo .env baseado no exemplo da plataforma"""
        env_example = f".env.{platform}.example"
        env_file = ".env"
        
        env_example_path = self.base_dir / env_example
        env_path = self.base_dir / env_file
        
        if not env_example_path.exists():
            print(f"❌ Arquivo {env_example} não encontrado")
            return False
        
        if env_path.exists():
            overwrite = input(f"📁 Arquivo .env já existe. Sobrescrever? (s/N): ").lower()
            if overwrite != 's':
                print("⏭️  Mantendo arquivo .env existente")
                return True
        
        try:
            with open(env_example_path, 'r', encoding='utf-8') as src:
                content = src.read()
            
            with open(env_path, 'w', encoding='utf-8') as dst:
                dst.write(content)
            
            print(f"✅ Arquivo .env criado baseado em {env_example}")
            print(f"⚠️  IMPORTANTE: Configure as variáveis em .env antes do deploy!")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao criar .env: {e}")
            return False

    def setup_git(self):
        """Configura repositório Git se necessário"""
        print("\n🔧 Configurando Git...")
        
        if not (self.base_dir / '.git').exists():
            try:
                subprocess.run(['git', 'init'], cwd=self.base_dir, check=True)
                print("✅ Repositório Git inicializado")
            except subprocess.CalledProcessError:
                print("❌ Erro ao inicializar Git")
                return False
        else:
            print("✅ Repositório Git já existe")
        
        # Verificar se há commits
        try:
            subprocess.run(['git', 'log', '--oneline', '-1'], 
                         cwd=self.base_dir, capture_output=True, check=True)
            print("✅ Repositório tem commits")
        except subprocess.CalledProcessError:
            print("⚠️  Repositório sem commits. Fazendo commit inicial...")
            try:
                subprocess.run(['git', 'add', '.'], cwd=self.base_dir, check=True)
                subprocess.run(['git', 'commit', '-m', 'Initial commit for hosting setup'], 
                             cwd=self.base_dir, check=True)
                print("✅ Commit inicial criado")
            except subprocess.CalledProcessError:
                print("❌ Erro ao criar commit inicial")
                return False
        
        return True

    def show_next_steps(self, platforms):
        """Exibe próximos passos para cada plataforma"""
        print("\n🎯 PRÓXIMOS PASSOS:")
        print("=" * 60)
        
        for platform in platforms:
            platform_info = self.platforms[platform]
            print(f"\n📋 {platform_info['name']}:")
            print(f"1. Acesse {platform_info['url']}")
            print("2. Crie uma conta gratuita")
            print("3. Conecte seu repositório GitHub")
            
            if platform == 'railway':
                print("4. Configure as variáveis de ambiente")
                print("5. Deploy automático será iniciado")
                print("6. Acesse via domínio .railway.app")
                
            elif platform == 'render':
                print("4. Crie um Web Service")
                print("5. Configure build command: ./build.sh")
                print("6. Configure start command: gunicorn sistema_imobiliario.wsgi:application")
                print("7. Adicione PostgreSQL database")
                print("8. Configure variáveis de ambiente")
                
            elif platform == 'heroku':
                print("4. Instale Heroku CLI")
                print("5. Execute: heroku create seu-app-name")
                print("6. Configure variáveis: heroku config:set")
                print("7. Adicione PostgreSQL: heroku addons:create heroku-postgresql:mini")
                print("8. Deploy: git push heroku main")
            
            print(f"📖 Guia completo: HOSPEDAGEM_GRATUITA_{platform.upper()}.md")

    def run_setup(self, platforms):
        """Executa configuração para as plataformas selecionadas"""
        print(f"\n🚀 Configurando para: {', '.join([self.platforms[p]['name'] for p in platforms])}")
        
        # Verificar arquivos
        all_files_ok = True
        for platform in platforms:
            files_status = self.check_files_exist(platform)
            if not all(files_status.values()):
                print(f"⚠️  Alguns arquivos para {platform} estão faltando")
                all_files_ok = False
        
        if not all_files_ok:
            print("\n❌ Execute o script novamente após criar os arquivos necessários")
            return False
        
        # Configurar Git
        if not self.setup_git():
            return False
        
        # Criar arquivo .env para a primeira plataforma
        if platforms:
            self.create_env_file(platforms[0])
        
        # Mostrar próximos passos
        self.show_next_steps(platforms)
        
        return True

    def main(self):
        """Função principal"""
        self.print_banner()
        
        if not self.check_requirements():
            return
        
        self.show_platforms()
        platforms = self.select_platform()
        
        if self.run_setup(platforms):
            print("\n✅ Configuração concluída com sucesso!")
            print("📚 Consulte os guias específicos para cada plataforma")
            print("🚀 Boa sorte com seu deploy!")
        else:
            print("\n❌ Configuração não foi concluída")

if __name__ == "__main__":
    setup = HospedagemGratuitaSetup()
    setup.main()