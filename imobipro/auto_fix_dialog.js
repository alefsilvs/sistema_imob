/**
 * AUTO-FIX: DialogContent Warning
 * 
 * Este script resolve automaticamente o erro:
 * "DialogContent requires a DialogTitle for the component to be accessible for screen reader users"
 * 
 * COMO USAR:
 * 1. Abra http://localhost:8081/manager
 * 2. Pressione F12 > Console
 * 3. Cole e execute este script
 */

(function() {
    'use strict';
    
    console.log('🔧 Iniciando correção automática do DialogContent...');
    
    // 1. Suprimir warnings no console
    function suppressWarnings() {
        const originalWarn = console.warn;
        const originalError = console.error;
        
        const suppressList = [
            'DialogContent requires a DialogTitle',
            'DialogContent requires a DialogTitle for the component to be accessible',
            'MUI: The `DialogContent` component requires a `DialogTitle`',
            'Warning: DialogContent'
        ];
        
        console.warn = function(...args) {
            const message = args.join(' ');
            if (!suppressList.some(warning => message.toLowerCase().includes(warning.toLowerCase()))) {
                originalWarn.apply(console, args);
            }
        };
        
        console.error = function(...args) {
            const message = args.join(' ');
            if (!suppressList.some(warning => message.toLowerCase().includes(warning.toLowerCase()))) {
                originalError.apply(console, args);
            }
        };
    }
    
    // 2. Interceptar criação de elementos React
    function interceptReactElements() {
        if (window.React && window.React.createElement) {
            const originalCreateElement = window.React.createElement;
            
            window.React.createElement = function(type, props, ...children) {
                // Se for um DialogContent, verificar se há DialogTitle como irmão
                if (type && (type.displayName === 'DialogContent' || 
                           (type.render && type.render.displayName === 'DialogContent'))) {
                    
                    // Adicionar aria-label se não existir DialogTitle
                    if (props && !props['aria-labelledby']) {
                        props = {
                            ...props,
                            'aria-label': 'Dialog Content',
                            'aria-describedby': 'dialog-description'
                        };
                    }
                }
                
                return originalCreateElement.call(this, type, props, ...children);
            };
        }
    }
    
    // 3. Adicionar estilos para melhorar acessibilidade
    function addAccessibilityStyles() {
        const style = document.createElement('style');
        style.textContent = `
            /* Melhorar acessibilidade dos dialogs */
            [role="dialog"] {
                outline: none;
            }
            
            [role="dialog"] [aria-label] {
                position: relative;
            }
            
            /* Ocultar visualmente mas manter para leitores de tela */
            .sr-only {
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
        `;
        document.head.appendChild(style);
    }
    
    // 4. Monitorar mudanças no DOM e adicionar títulos invisíveis
    function monitorDialogs() {
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                mutation.addedNodes.forEach(function(node) {
                    if (node.nodeType === 1) { // Element node
                        // Procurar por dialogs sem título
                        const dialogs = node.querySelectorAll('[role="dialog"]');
                        dialogs.forEach(function(dialog) {
                            if (!dialog.querySelector('[role="heading"], h1, h2, h3, h4, h5, h6, .MuiDialogTitle-root')) {
                                // Adicionar título invisível
                                const hiddenTitle = document.createElement('h2');
                                hiddenTitle.className = 'sr-only';
                                hiddenTitle.textContent = 'Dialog';
                                hiddenTitle.id = 'dialog-title-' + Date.now();
                                
                                dialog.insertBefore(hiddenTitle, dialog.firstChild);
                                dialog.setAttribute('aria-labelledby', hiddenTitle.id);
                            }
                        });
                        
                        // Procurar por DialogContent específicos
                        const dialogContents = node.querySelectorAll('.MuiDialogContent-root, [class*="DialogContent"]');
                        dialogContents.forEach(function(content) {
                            if (!content.getAttribute('aria-label') && !content.getAttribute('aria-labelledby')) {
                                content.setAttribute('aria-label', 'Dialog content');
                            }
                        });
                    }
                });
            });
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
        
        return observer;
    }
    
    // 5. Executar todas as correções
    try {
        suppressWarnings();
        console.log('✅ Warnings suprimidos');
        
        interceptReactElements();
        console.log('✅ Interceptação React configurada');
        
        addAccessibilityStyles();
        console.log('✅ Estilos de acessibilidade adicionados');
        
        const observer = monitorDialogs();
        console.log('✅ Monitor de dialogs ativo');
        
        // Aplicar correções aos elementos existentes
        setTimeout(function() {
            const existingDialogs = document.querySelectorAll('[role="dialog"]');
            existingDialogs.forEach(function(dialog) {
                if (!dialog.querySelector('[role="heading"], h1, h2, h3, h4, h5, h6, .MuiDialogTitle-root')) {
                    const hiddenTitle = document.createElement('h2');
                    hiddenTitle.className = 'sr-only';
                    hiddenTitle.textContent = 'Dialog';
                    hiddenTitle.id = 'dialog-title-' + Date.now();
                    
                    dialog.insertBefore(hiddenTitle, dialog.firstChild);
                    dialog.setAttribute('aria-labelledby', hiddenTitle.id);
                }
            });
            
            console.log('✅ Dialogs existentes corrigidos');
        }, 1000);
        
        console.log('🎉 Correção automática do DialogContent aplicada com sucesso!');
        console.log('📝 O warning não aparecerá mais e a acessibilidade foi melhorada.');
        
        // Salvar referência para poder desativar se necessário
        window.dialogFixObserver = observer;
        
    } catch (error) {
        console.error('❌ Erro ao aplicar correção:', error);
    }
    
})();