#!/usr/bin/env node

/**
 * Script para encontrar e corrigir problemas de acessibilidade em componentes Dialog
 * Uso: node fix_dialog_accessibility.js [diretório]
 */

const fs = require('fs');
const path = require('path');

// Extensões de arquivo para verificar
const EXTENSIONS = ['.js', '.jsx', '.ts', '.tsx'];

// Padrões para encontrar problemas
const PATTERNS = {
  dialogContent: /<DialogContent[\s\S]*?>/g,
  dialogTitle: /<DialogTitle[\s\S]*?>/g,
  dialog: /<Dialog[\s\S]*?>/g
};

class DialogAccessibilityFixer {
  constructor(rootDir = '.') {
    this.rootDir = rootDir;
    this.issues = [];
  }

  // Encontra todos os arquivos relevantes
  findFiles(dir = this.rootDir) {
    const files = [];
    
    try {
      const items = fs.readdirSync(dir);
      
      for (const item of items) {
        const fullPath = path.join(dir, item);
        const stat = fs.statSync(fullPath);
        
        if (stat.isDirectory() && !item.startsWith('.') && item !== 'node_modules') {
          files.push(...this.findFiles(fullPath));
        } else if (stat.isFile() && EXTENSIONS.some(ext => item.endsWith(ext))) {
          files.push(fullPath);
        }
      }
    } catch (error) {
      console.warn(`Erro ao ler diretório ${dir}:`, error.message);
    }
    
    return files;
  }

  // Analisa um arquivo em busca de problemas
  analyzeFile(filePath) {
    try {
      const content = fs.readFileSync(filePath, 'utf8');
      const issues = [];

      // Encontra todos os DialogContent
      const dialogContents = [...content.matchAll(PATTERNS.dialogContent)];
      const dialogTitles = [...content.matchAll(PATTERNS.dialogTitle)];
      
      if (dialogContents.length > 0) {
        // Verifica se há DialogTitle correspondente
        if (dialogTitles.length === 0) {
          issues.push({
            type: 'missing_dialog_title',
            file: filePath,
            line: this.getLineNumber(content, dialogContents[0].index),
            message: 'DialogContent encontrado sem DialogTitle correspondente',
            suggestion: 'Adicione um DialogTitle antes do DialogContent'
          });
        }

        // Verifica proporção DialogContent vs DialogTitle
        if (dialogContents.length > dialogTitles.length) {
          issues.push({
            type: 'unbalanced_dialog_components',
            file: filePath,
            line: this.getLineNumber(content, dialogContents[0].index),
            message: `${dialogContents.length} DialogContent(s) mas apenas ${dialogTitles.length} DialogTitle(s)`,
            suggestion: 'Verifique se cada DialogContent tem um DialogTitle correspondente'
          });
        }
      }

      return issues;
    } catch (error) {
      console.warn(`Erro ao analisar arquivo ${filePath}:`, error.message);
      return [];
    }
  }

  // Obtém o número da linha de um índice
  getLineNumber(content, index) {
    return content.substring(0, index).split('\n').length;
  }

  // Gera sugestão de correção
  generateFix(issue) {
    switch (issue.type) {
      case 'missing_dialog_title':
        return `
// Adicione antes do DialogContent:
<DialogTitle>
  Título do Diálogo
</DialogTitle>

// Ou se não quiser título visível:
<DialogTitle sx={{ display: 'none' }}>
  Título para leitores de tela
</DialogTitle>
`;

      case 'unbalanced_dialog_components':
        return `
// Verifique se cada Dialog tem esta estrutura:
<Dialog open={open} onClose={handleClose}>
  <DialogTitle>Título</DialogTitle>
  <DialogContent>
    Conteúdo
  </DialogContent>
  <DialogActions>
    Ações
  </DialogActions>
</Dialog>
`;

      default:
        return 'Consulte a documentação para mais detalhes.';
    }
  }

  // Executa a análise completa
  run() {
    console.log('🔍 Procurando problemas de acessibilidade em componentes Dialog...\n');
    
    const files = this.findFiles();
    console.log(`📁 Analisando ${files.length} arquivos...\n`);

    let totalIssues = 0;

    for (const file of files) {
      const issues = this.analyzeFile(file);
      
      if (issues.length > 0) {
        console.log(`❌ ${file}:`);
        
        for (const issue of issues) {
          console.log(`   Linha ${issue.line}: ${issue.message}`);
          console.log(`   💡 ${issue.suggestion}\n`);
          totalIssues++;
        }
      }
    }

    if (totalIssues === 0) {
      console.log('✅ Nenhum problema de acessibilidade encontrado!');
    } else {
      console.log(`\n📊 Resumo: ${totalIssues} problema(s) encontrado(s) em ${files.length} arquivo(s)`);
      console.log('\n🛠️  Para corrigir:');
      console.log('1. Adicione DialogTitle a cada Dialog que contém DialogContent');
      console.log('2. Use sx={{ display: "none" }} se não quiser título visível');
      console.log('3. Considere usar aria-labelledby para melhor acessibilidade');
      console.log('\n📖 Consulte dialog_accessibility_fix.md para exemplos detalhados');
    }

    return totalIssues;
  }
}

// Executa o script
if (require.main === module) {
  const targetDir = process.argv[2] || '.';
  const fixer = new DialogAccessibilityFixer(targetDir);
  
  try {
    const issueCount = fixer.run();
    process.exit(issueCount > 0 ? 1 : 0);
  } catch (error) {
    console.error('❌ Erro ao executar análise:', error.message);
    process.exit(1);
  }
}

module.exports = DialogAccessibilityFixer;