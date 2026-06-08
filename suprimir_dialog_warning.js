/**
 * Script para suprimir o warning de DialogContent no Evolution Manager
 * 
 * Este script injeta código no navegador para suprimir o warning:
 * "DialogContent requires a DialogTitle for the component to be accessible for screen reader users."
 * 
 * O warning vem do Evolution Manager (React compilado) e não afeta a funcionalidade.
 */

// Função para suprimir warnings específicos
function suprimirDialogWarning() {
    // Salvar a função console.warn original
    const originalWarn = console.warn;
    
    // Substituir console.warn por uma versão filtrada
    console.warn = function(...args) {
        // Converter argumentos para string para verificação
        const message = args.join(' ');
        
        // Lista de warnings para suprimir
        const warningsParaSuprimir = [
            'DialogContent requires a DialogTitle',
            'DialogContent requires a DialogTitle for the component to be accessible',
            'MUI: The `DialogContent` component requires a `DialogTitle`'
        ];
        
        // Verificar se a mensagem contém algum warning para suprimir
        const deveSuprimir = warningsParaSuprimir.some(warning => 
            message.includes(warning)
        );
        
        // Se não deve suprimir, mostrar o warning normalmente
        if (!deveSuprimir) {
            originalWarn.apply(console, args);
        }
    };
    
    console.log('✅ Warning de DialogContent suprimido com sucesso!');
}

// Função para restaurar warnings originais
function restaurarWarnings() {
    // Recarregar a página para restaurar console.warn original
    location.reload();
}

// Executar automaticamente quando o script for carregado
if (typeof window !== 'undefined') {
    // Aguardar o DOM carregar
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', suprimirDialogWarning);
    } else {
        suprimirDialogWarning();
    }
}

// Exportar funções para uso manual
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        suprimirDialogWarning,
        restaurarWarnings
    };
}

// Adicionar ao objeto global para uso no console do navegador
if (typeof window !== 'undefined') {
    window.DialogWarningFix = {
        suprimir: suprimirDialogWarning,
        restaurar: restaurarWarnings
    };
}