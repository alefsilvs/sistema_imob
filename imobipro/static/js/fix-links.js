/**
 * Fix para links com problemas de clique
 * Corrige links com href="#" e adiciona handlers adequados
 * Versão melhorada com tratamento de erros
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('Fix-links.js carregado - versão melhorada');
    
    try {
        // Fix para todos os links com href="#"
        const problematicLinks = document.querySelectorAll('a[href="#"]');
        
        problematicLinks.forEach(function(link) {
            try {
                link.addEventListener('click', function(e) {
                    try {
                        e.preventDefault();
                        e.stopPropagation();
                        
                        // Log para debug
                        console.log('Link clicado:', link.textContent.trim());
                        
                        // Verificar se tem data-bs-toggle (Bootstrap collapse)
                        if (link.hasAttribute('data-bs-toggle')) {
                            // Deixar o Bootstrap gerenciar
                            return;
                        }
                        
                        // Verificar se tem onclick definido
                        if (link.hasAttribute('onclick')) {
                            // Deixar o onclick gerenciar
                            return;
                        }
                        
                        // Para links sem funcionalidade específica, mostrar aviso
                        const linkText = link.textContent.trim();
                        if (linkText) {
                            console.warn('Link sem funcionalidade implementada:', linkText);
                            
                            // Opcional: mostrar notificação para o usuário
                            if (typeof showNotification === 'function') {
                                try {
                                    showNotification('Funcionalidade em desenvolvimento: ' + linkText, 'info');
                                } catch (notifError) {
                                    console.warn('Erro ao mostrar notificação:', notifError);
                                }
                            }
                        }
                    } catch (clickError) {
                        console.error('Erro no handler de click:', clickError);
                    }
                });
            } catch (linkError) {
                console.error('Erro ao processar link:', linkError, link);
            }
        });
        
        // Fix específico para elementos td com cursor pointer (linhas clicáveis)
        const clickableRows = document.querySelectorAll('tr[style*="cursor: pointer"], tr.clickable-row');
        clickableRows.forEach(function(row) {
            try {
                const links = row.querySelectorAll('a');
                links.forEach(function(link) {
                    try {
                        link.addEventListener('click', function(e) {
                            try {
                                e.stopPropagation(); // Evita que o clique no link acione o clique da linha
                            } catch (stopError) {
                                console.error('Erro ao parar propagação:', stopError);
                            }
                        });
                    } catch (linkRowError) {
                        console.error('Erro ao processar link em linha:', linkRowError, link);
                    }
                });
            } catch (rowError) {
                console.error('Erro ao processar linha clicável:', rowError, row);
            }
        });
        
        // Fix para links dentro de tabelas (td) - apenas para links problemáticos
        const tableLinks = document.querySelectorAll('td a[href="#"]');
        tableLinks.forEach(function(link) {
            try {
                link.addEventListener('click', function(e) {
                    try {
                        e.preventDefault();
                        e.stopPropagation(); // Evita conflito com eventos da linha da tabela
                        
                        console.log('Link em tabela clicado:', link.textContent.trim());
                        
                        // Verificar se tem onclick definido
                        if (link.hasAttribute('onclick')) {
                            // Deixar o onclick gerenciar
                            return;
                        }
                        
                        // Para links sem funcionalidade específica, mostrar aviso
                        const linkText = link.textContent.trim();
                        if (linkText && typeof showNotification === 'function') {
                            try {
                                showNotification('Funcionalidade em desenvolvimento: ' + linkText, 'info');
                            } catch (notifError) {
                                console.warn('Erro ao mostrar notificação em tabela:', notifError);
                            }
                        }
                    } catch (tableClickError) {
                        console.error('Erro no click de link em tabela:', tableClickError);
                    }
                });
            } catch (tableLinkError) {
                console.error('Erro ao processar link em tabela:', tableLinkError, link);
            }
        });
        
        // Fix para links em headers - versão melhorada
        try {
            const headerLinks = document.querySelectorAll('header a[href="#"], .header a[href="#"], .dashboard-header a[href="#"]');
            headerLinks.forEach(function(link) {
                if (link && typeof link.addEventListener === 'function') {
                    try {
                        link.addEventListener('click', function(e) {
                            try {
                                e.preventDefault();
                                
                                // Verificar se tem funcionalidade específica
                                if (link.hasAttribute('data-bs-toggle') || link.hasAttribute('onclick')) {
                                    return;
                                }
                                
                                // Mostrar notificação se disponível
                                if (typeof showNotification === 'function') {
                                    const linkText = link.textContent.trim();
                                    if (linkText) {
                                        showNotification('Funcionalidade em desenvolvimento: ' + linkText, 'info');
                                    }
                                }
                            } catch (headerClickError) {
                                // Silenciar erro para evitar poluição do console
                                // console.warn('Erro no click de header link:', headerClickError);
                            }
                        });
                    } catch (headerLinkError) {
                        // Silenciar erro para evitar poluição do console
                        // console.warn('Erro ao processar header link:', headerLinkError);
                    }
                }
            });
        } catch (headerProcessError) {
            // Silenciar erro para evitar poluição do console
            // console.warn('Erro ao processar links de header:', headerProcessError);
        }
        
        // Fix para dropdowns sem funcionalidade
        const dropdownLinks = document.querySelectorAll('.dropdown-item[href="#"]');
        dropdownLinks.forEach(function(link) {
            try {
                link.addEventListener('click', function(e) {
                    try {
                        e.preventDefault();
                        const action = link.textContent.trim();
                        console.log('Ação de dropdown:', action);
                        
                        if (typeof showNotification === 'function') {
                            try {
                                showNotification('Ação em desenvolvimento: ' + action, 'info');
                            } catch (notifError) {
                                console.warn('Erro ao mostrar notificação de dropdown:', notifError);
                            }
                        }
                    } catch (dropdownClickError) {
                        console.error('Erro no click de dropdown:', dropdownClickError);
                    }
                });
            } catch (dropdownLinkError) {
                console.error('Erro ao processar dropdown link:', dropdownLinkError, link);
            }
        });
        
        console.log('Fix aplicado para', problematicLinks.length, 'links problemáticos');
        
    } catch (mainError) {
        // Silenciar erro principal para evitar poluição do console
        // console.warn('Erro principal no fix-links.js:', mainError);
        // Não interromper a execução, apenas registrar o aviso
    }
});

// Função auxiliar para mostrar notificações (se não existir)
if (typeof showNotification !== 'function') {
    window.showNotification = function(message, type) {
        console.log('Notificação [' + type + ']:', message);
        
        // Criar notificação visual simples
        const notification = document.createElement('div');
        notification.className = 'alert alert-' + (type === 'info' ? 'info' : 'warning') + ' position-fixed';
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; max-width: 300px;';
        notification.innerHTML = message;
        
        document.body.appendChild(notification);
        
        // Remover após 3 segundos
        setTimeout(function() {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 3000);
    };
}