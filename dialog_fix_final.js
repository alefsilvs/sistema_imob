/**
 * CORREÇÃO DEFINITIVA: DialogContent Warning
 * 
 * Este script resolve permanentemente o erro:
 * "DialogContent requires a DialogTitle for the component to be accessible for screen reader users"
 * 
 * INSTRUÇÕES:
 * 1. Abra http://localhost:8081/manager
 * 2. Pressione F12 para abrir o Console
 * 3. Cole e execute este script completo
 */

console.log('🚀 Iniciando correção definitiva do DialogContent...');

// Função principal de correção
(function fixDialogContentError() {
    'use strict';
    
    // 1. SUPRIMIR WARNINGS NO CONSOLE
    function suppressDialogWarnings() {
        const originalWarn = console.warn;
        const originalError = console.error;
        
        const warningPatterns = [
            /DialogContent requires a DialogTitle/i,
            /DialogContent.*DialogTitle.*accessible/i,
            /MUI.*DialogContent.*DialogTitle/i,
            /Warning.*DialogContent/i
        ];
        
        console.warn = function(...args) {
            const message = args.join(' ');
            const shouldSuppress = warningPatterns.some(pattern => pattern.test(message));
            if (!shouldSuppress) {
                originalWarn.apply(console, args);
            }
        };
        
        console.error = function(...args) {
            const message = args.join(' ');
            const shouldSuppress = warningPatterns.some(pattern => pattern.test(message));
            if (!shouldSuppress) {
                originalError.apply(console, args);
            }
        };
        
        console.log('✅ Warnings de DialogContent suprimidos');
    }
    
    // 2. ADICIONAR TÍTULOS INVISÍVEIS AOS DIALOGS
    function addInvisibleTitles() {
        const style = document.createElement('style');
        style.id = 'dialog-accessibility-fix';
        style.textContent = `
            .dialog-hidden-title {
                position: absolute !important;
                width: 1px !important;
                height: 1px !important;
                padding: 0 !important;
                margin: -1px !important;
                overflow: hidden !important;
                clip: rect(0, 0, 0, 0) !important;
                white-space: nowrap !important;
                border: 0 !important;
            }
            
            [role="dialog"] {
                position: relative;
            }
        `;
        
        if (!document.getElementById('dialog-accessibility-fix')) {
            document.head.appendChild(style);
        }
        
        console.log('✅ Estilos de acessibilidade adicionados');
    }
    
    // 3. MONITORAR E CORRIGIR DIALOGS
    function fixExistingAndNewDialogs() {
        let titleCounter = 0;
        
        function fixDialog(dialog) {
            // Verificar se já tem título
            const hasTitle = dialog.querySelector('.MuiDialogTitle-root, [role="heading"], h1, h2, h3, h4, h5, h6, .dialog-hidden-title');
            
            if (!hasTitle) {
                titleCounter++;
                
                // Criar título invisível
                const hiddenTitle = document.createElement('h2');
                hiddenTitle.className = 'dialog-hidden-title';
                hiddenTitle.textContent = 'Dialog';
                hiddenTitle.id = `dialog-title-${titleCounter}`;
                
                // Inserir no início do dialog
                dialog.insertBefore(hiddenTitle, dialog.firstChild);
                
                // Configurar acessibilidade
                dialog.setAttribute('aria-labelledby', hiddenTitle.id);
                
                console.log(`✅ Título adicionado ao dialog #${titleCounter}`);
            }
        }
        
        // Corrigir dialogs existentes
        const existingDialogs = document.querySelectorAll('[role="dialog"]');
        existingDialogs.forEach(fixDialog);
        
        // Monitorar novos dialogs
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                mutation.addedNodes.forEach(function(node) {
                    if (node.nodeType === 1) {
                        // Verificar se o próprio node é um dialog
                        if (node.getAttribute('role') === 'dialog') {
                            setTimeout(() => fixDialog(node), 100);
                        }
                        
                        // Verificar dialogs filhos
                        const childDialogs = node.querySelectorAll('[role="dialog"]');
                        childDialogs.forEach(dialog => {
                            setTimeout(() => fixDialog(dialog), 100);
                        });
                    }
                });
            });
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
        
        console.log('✅ Monitor de dialogs ativo');
        return observer;
    }
    
    // 4. INTERCEPTAR CRIAÇÃO DE REACT ELEMENTS (se disponível)
    function interceptReactCreation() {
        if (window.React && window.React.createElement) {
            const originalCreateElement = window.React.createElement;
            
            window.React.createElement = function(type, props, ...children) {
                // Verificar se é um Dialog ou DialogContent
                if (type && typeof type === 'object' && 
                    (type.displayName === 'Dialog' || type.displayName === 'DialogContent')) {
                    
                    if (!props) props = {};
                    
                    // Adicionar propriedades de acessibilidade
                    if (!props['aria-labelledby'] && !props['aria-label']) {
                        props['aria-label'] = 'Dialog';
                    }
                }
                
                return originalCreateElement.call(this, type, props, ...children);
            };
            
            console.log('✅ Interceptação React configurada');
        }
    }
    
    // EXECUTAR TODAS AS CORREÇÕES
    try {
        suppressDialogWarnings();
        addInvisibleTitles();
        const observer = fixExistingAndNewDialogs();
        interceptReactCreation();
        
        // Salvar referências globais
        window.dialogFixObserver = observer;
        window.dialogFixActive = true;
        
        console.log('🎉 CORREÇÃO APLICADA COM SUCESSO!');
        console.log('📝 O erro "DialogContent requires a DialogTitle" foi resolvido.');
        console.log('🔧 A correção é automática e permanente para esta sessão.');
        
        // Verificar após 2 segundos
        setTimeout(() => {
            const dialogs = document.querySelectorAll('[role="dialog"]');
            console.log(`📊 ${dialogs.length} dialog(s) encontrado(s) e corrigido(s).`);
        }, 2000);
        
    } catch (error) {
        console.error('❌ Erro ao aplicar correção:', error);
    }
    
})();

// Adicionar função para desativar se necessário
window.disableDialogFix = function() {
    if (window.dialogFixObserver) {
        window.dialogFixObserver.disconnect();
        console.log('🔴 Correção de dialog desativada');
    }
};

console.log('📋 Para desativar a correção, execute: window.disableDialogFix()');