#!/usr/bin/env node

/**
 * Script de diagnóstico para identificar problemas de DialogContent
 * Este script ajuda a encontrar a origem do erro de acessibilidade
 */

const fs = require('fs');
const path = require('path');

class DialogErrorDiagnostic {
  constructor() {
    this.findings = [];
  }

  // Verifica arquivos de configuração e dependências
  checkDependencies() {
    console.log('🔍 Verificando dependências...\n');

    const packageFiles = ['package.json', 'package-lock.json', 'yarn.lock'];
    
    for (const file of packageFiles) {
      if (fs.existsSync(file)) {
        try {
          const content = fs.readFileSync(file, 'utf8');
          
          // Procura por bibliotecas de UI que usam Dialog
          const uiLibraries = [
            '@mui/material',
            '@material-ui/core',
            'antd',
            'react-bootstrap',
            'semantic-ui-react',
            'chakra-ui',
            'mantine'
          ];

          for (const lib of uiLibraries) {
            if (content.includes(lib)) {
              console.log(`📦 Encontrada dependência: ${lib}`);
              this.findings.push(`Biblioteca UI encontrada: ${lib}`);
            }
          }
        } catch (error) {
          console.warn(`Erro ao ler ${file}:`, error.message);
        }
      }
    }
  }

  // Verifica arquivos HTML que podem conter React
  checkHtmlFiles() {
    console.log('\n🔍 Verificando arquivos HTML...\n');

    const htmlFiles = this.findFilesByExtension(['.html']);
    
    for (const file of htmlFiles) {
      try {
        const content = fs.readFileSync(file, 'utf8');
        
        // Procura por indicações de React/Dialog
        const patterns = [
          'react',
          'dialog',
          'modal',
          'DialogContent',
          'DialogTitle',
          'mui',
          'material-ui'
        ];

        for (const pattern of patterns) {
          if (content.toLowerCase().includes(pattern.toLowerCase())) {
            console.log(`📄 ${file}: Contém "${pattern}"`);
            this.findings.push(`HTML com ${pattern}: ${file}`);
          }
        }
      } catch (error) {
        console.warn(`Erro ao ler ${file}:`, error.message);
      }
    }
  }

  // Verifica logs e arquivos de erro
  checkLogs() {
    console.log('\n🔍 Verificando logs...\n');

    const logDirs = ['logs', 'log', '.'];
    const logExtensions = ['.log', '.err', '.out'];

    for (const dir of logDirs) {
      if (fs.existsSync(dir)) {
        try {
          const files = fs.readdirSync(dir);
          
          for (const file of files) {
            if (logExtensions.some(ext => file.endsWith(ext))) {
              const filePath = path.join(dir, file);
              try {
                const content = fs.readFileSync(filePath, 'utf8');
                
                if (content.includes('DialogContent') || content.includes('DialogTitle')) {
                  console.log(`📋 Log com erro de Dialog: ${filePath}`);
                  this.findings.push(`Log com erro: ${filePath}`);
                }
              } catch (error) {
                // Arquivo pode estar em uso, ignorar
              }
            }
          }
        } catch (error) {
          console.warn(`Erro ao ler diretório ${dir}:`, error.message);
        }
      }
    }
  }

  // Verifica processos Node.js em execução
  checkRunningProcesses() {
    console.log('\n🔍 Verificando processos em execução...\n');

    try {
      const { execSync } = require('child_process');
      
      // Lista processos Node.js
      const processes = execSync('tasklist /FI "IMAGENAME eq node.exe" /FO CSV', { encoding: 'utf8' });
      
      if (processes.includes('node.exe')) {
        console.log('🟢 Processos Node.js encontrados em execução');
        console.log('💡 O erro pode estar vindo de uma aplicação React em execução');
        this.findings.push('Processos Node.js ativos encontrados');
      }
    } catch (error) {
      console.warn('Não foi possível verificar processos:', error.message);
    }
  }

  // Encontra arquivos por extensão
  findFilesByExtension(extensions, dir = '.', maxDepth = 3, currentDepth = 0) {
    const files = [];
    
    if (currentDepth >= maxDepth) return files;

    try {
      const items = fs.readdirSync(dir);
      
      for (const item of items) {
        if (item.startsWith('.') || item === 'node_modules') continue;
        
        const fullPath = path.join(dir, item);
        const stat = fs.statSync(fullPath);
        
        if (stat.isDirectory()) {
          files.push(...this.findFilesByExtension(extensions, fullPath, maxDepth, currentDepth + 1));
        } else if (extensions.some(ext => item.endsWith(ext))) {
          files.push(fullPath);
        }
      }
    } catch (error) {
      // Ignorar erros de permissão
    }
    
    return files;
  }

  // Gera relatório de diagnóstico
  generateReport() {
    console.log('\n📊 RELATÓRIO DE DIAGNÓSTICO\n');
    console.log('=' * 50);

    if (this.findings.length === 0) {
      console.log('❓ Nenhuma evidência clara encontrada nos arquivos locais.');
      console.log('\n🔍 POSSÍVEIS ORIGENS DO ERRO:');
      console.log('1. Console do navegador (F12 > Console)');
      console.log('2. Aplicação React em execução');
      console.log('3. Extensão do navegador');
      console.log('4. Biblioteca externa');
    } else {
      console.log('🔍 EVIDÊNCIAS ENCONTRADAS:');
      for (const finding of this.findings) {
        console.log(`• ${finding}`);
      }
    }

    console.log('\n🛠️  PRÓXIMOS PASSOS:');
    console.log('1. Abra o navegador e pressione F12');
    console.log('2. Vá para a aba Console');
    console.log('3. Procure pelo erro "DialogContent requires a DialogTitle"');
    console.log('4. Clique no erro para ver o stack trace');
    console.log('5. Identifique o arquivo e linha específicos');

    console.log('\n💡 SOLUÇÕES RÁPIDAS:');
    console.log('• Se for Material-UI: Adicione <DialogTitle> antes de <DialogContent>');
    console.log('• Se for Ant Design: Use Modal.confirm() ou adicione title prop');
    console.log('• Se for React Bootstrap: Use Modal.Header com Modal.Title');

    console.log('\n📖 Consulte dialog_accessibility_fix.md para exemplos detalhados');
  }

  // Executa diagnóstico completo
  run() {
    console.log('🚀 DIAGNÓSTICO DE ERRO DE DIALOG\n');
    console.log('Procurando a origem do erro: "DialogContent requires a DialogTitle"\n');

    this.checkDependencies();
    this.checkHtmlFiles();
    this.checkLogs();
    this.checkRunningProcesses();
    this.generateReport();
  }
}

// Executa o diagnóstico
if (require.main === module) {
  const diagnostic = new DialogErrorDiagnostic();
  diagnostic.run();
}

module.exports = DialogErrorDiagnostic;