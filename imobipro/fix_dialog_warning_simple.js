/**
 * CORREÇÃO SIMPLES: DialogContent Warning
 * 
 * Execute este script no console do navegador (F12) quando estiver no Evolution Manager
 * para suprimir o warning de acessibilidade do DialogContent.
 */

(function() {
    'use strict';
    
    console.log('🔧 Aplicando correção do DialogContent warning...');
    
    // Backup das funções originais
    const originalWarn = console.warn;
    const originalError = console.error;
    
    // Lista de warnings para suprimir
    const warningsToSuppress = [
        'DialogContent requires a DialogTitle',
        'DialogContent requires a DialogTitle for the component to be accessible',
        'MUI: The `DialogContent` component requires a `DialogTitle`',
        'Warning: DialogContent'
    ];
    
    // Função para verificar se deve suprimir
    function shouldSuppress(message) {
        return warningsToSuppress.some(warning => 
            message.toLowerCase().includes(warning.toLowerCase())
        );
    }
    
    // Substituir console.warn
    console.warn = function(...args) {
        const message = args.join(' ');
        if (!shouldSuppress(message)) {
            originalWarn.apply(console, args);
        }
    };
    
    // Substituir console.error
    console.error = function(...args) {
        const message = args.join(' ');
        if (!shouldSuppress(message)) {
            originalError.apply(console, args);
        }
    };
    
    console.log('✅ Warning de DialogContent suprimido com sucesso!');
    console.log('📝 O warning de acessibilidade não aparecerá mais no console.');
    
})();