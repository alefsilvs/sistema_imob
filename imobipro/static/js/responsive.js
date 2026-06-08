/* ===== SISTEMA RESPONSIVO JAVASCRIPT ===== */

/* ===== FUNÇÕES GLOBAIS ===== */
// Definir showModal globalmente para evitar ReferenceError
window.showModal = function(title, content, buttons = []) {
    const modal = createModal(title, content, buttons);
    document.body.appendChild(modal);
    
    setTimeout(() => {
        modal.classList.add('show');
    }, 10);
    
    return modal;
};

window.hideModal = function(modal) {
    modal.classList.remove('show');
    setTimeout(() => {
        if (modal.parentNode) {
            modal.parentNode.removeChild(modal);
        }
    }, 300);
};

// Função para criar modal
function createModal(title, content, buttons = []) {
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.innerHTML = `
        <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">${title}</h5>
                    <button type="button" class="btn-close" onclick="hideModal(this.closest('.modal'))"></button>
                </div>
                <div class="modal-body">
                    ${content}
                </div>
                <div class="modal-footer">
                    ${buttons.map(btn => `<button type="button" class="btn ${btn.class}" onclick="${btn.action ? btn.action.toString() : ''}">${btn.text}</button>`).join('')}
                </div>
            </div>
        </div>
    `;
    return modal;
}

// Inicialização quando o DOM estiver carregado
document.addEventListener('DOMContentLoaded', function() {
    initializeResponsiveFeatures();
    initializeNavigation();
    initializeModals();
    initializeForms();
    initializeTooltips();
    initializeTables();
    initializeCharts();
    initializePWA();
});

/* ===== FUNCIONALIDADES RESPONSIVAS ===== */
function initializeResponsiveFeatures() {
    // Detectar tipo de dispositivo
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    const isTablet = /iPad|Android/i.test(navigator.userAgent) && window.innerWidth >= 768;
    const isDesktop = window.innerWidth >= 992;
    
    // Adicionar classes ao body
    document.body.classList.add(isMobile ? 'mobile' : isTablet ? 'tablet' : 'desktop');
    
    // Configurar viewport para mobile
    if (isMobile) {
        let viewport = document.querySelector('meta[name=viewport]');
        if (!viewport) {
            viewport = document.createElement('meta');
            viewport.name = 'viewport';
            document.head.appendChild(viewport);
        }
        viewport.content = 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no';
    }
    
    // Listener para mudanças de orientação
    window.addEventListener('orientationchange', function() {
        setTimeout(function() {
            window.location.reload();
        }, 500);
    });
    
    // Listener para redimensionamento
    let resizeTimer;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(function() {
            updateResponsiveElements();
        }, 250);
    });
}

function updateResponsiveElements() {
    // Atualizar gráficos
    if (window.Chart) {
        Chart.helpers.each(Chart.instances, function(instance) {
            instance.resize();
        });
    }
    
    // Atualizar tabelas responsivas
    updateResponsiveTables();
    
    // Atualizar navegação
    updateNavigation();
}

/* ===== NAVEGAÇÃO RESPONSIVA ===== */
function initializeNavigation() {
    const navbarToggler = document.querySelector('.navbar-toggler');
    const navbarCollapse = document.querySelector('.navbar-collapse');
    
    if (navbarToggler && navbarCollapse) {
        navbarToggler.addEventListener('click', function() {
            navbarCollapse.classList.toggle('show');
            
            // Atualizar ícone do botão
            const icon = navbarToggler.querySelector('i');
            if (icon) {
                icon.classList.toggle('fa-bars');
                icon.classList.toggle('fa-times');
            }
        });
        
        // Fechar menu ao clicar em link (mobile)
        const navLinks = navbarCollapse.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.addEventListener('click', function() {
                if (window.innerWidth < 768) {
                    navbarCollapse.classList.remove('show');
                    const icon = navbarToggler.querySelector('i');
                    if (icon) {
                        icon.classList.add('fa-bars');
                        icon.classList.remove('fa-times');
                    }
                }
            });
        });
        
        // Fechar menu ao clicar fora
        document.addEventListener('click', function(e) {
            if (!navbarToggler.contains(e.target) && !navbarCollapse.contains(e.target)) {
                navbarCollapse.classList.remove('show');
                const icon = navbarToggler.querySelector('i');
                if (icon) {
                    icon.classList.add('fa-bars');
                    icon.classList.remove('fa-times');
                }
            }
        });
    }
}

function updateNavigation() {
    const navbarCollapse = document.querySelector('.navbar-collapse');
    if (navbarCollapse && window.innerWidth >= 768) {
        navbarCollapse.classList.remove('show');
    }
}

/* ===== MODAIS RESPONSIVOS ===== */
function initializeModals() {
    // As funções showModal e hideModal já estão definidas globalmente
    
    // Confirmar ações
    window.confirmAction = function(message, callback) {
        const modal = showModal(
            'Confirmação',
            `<p>${message}</p>`,
            [
                {
                    text: 'Cancelar',
                    class: 'btn-secondary',
                    action: function(modal) {
                        hideModal(modal);
                    }
                },
                {
                    text: 'Confirmar',
                    class: 'btn-primary',
                    action: function(modal) {
                        hideModal(modal);
                        if (callback) callback();
                    }
                }
            ]
        );
    };
    
    // Mostrar alertas
    window.showAlert = function(message, type = 'info', duration = 5000) {
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade-in`;
        alert.innerHTML = `
            <i class="fas fa-${getAlertIcon(type)}"></i>
            ${message}
            <button type="button" class="btn-close" onclick="this.parentNode.remove()">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        // Adicionar ao topo da página
        const container = document.querySelector('.container, .container-fluid, body');
        container.insertBefore(alert, container.firstChild);
        
        // Remover automaticamente
        if (duration > 0) {
            setTimeout(() => {
                if (alert.parentNode) {
                    alert.remove();
                }
            }, duration);
        }
    };
}

function createModal(title, content, buttons) {
    const modal = document.createElement('div');
    modal.className = 'modal';
    
    const buttonsHtml = buttons.map(btn => 
        `<button type="button" class="btn ${btn.class}" data-action="${btn.action}">${btn.text}</button>`
    ).join('');
    
    modal.innerHTML = `
        <div class="modal-dialog">
            <div class="modal-header">
                <h5 class="modal-title">${title}</h5>
                <button type="button" class="btn-close" onclick="hideModal(this.closest('.modal'))">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="modal-body">
                ${content}
            </div>
            ${buttons.length > 0 ? `<div class="modal-footer">${buttonsHtml}</div>` : ''}
        </div>
    `;
    
    // Adicionar eventos aos botões
    buttons.forEach((btn, index) => {
        const button = modal.querySelectorAll('.modal-footer .btn')[index];
        if (button && btn.action) {
            button.addEventListener('click', () => btn.action(modal));
        }
    });
    
    // Fechar ao clicar no fundo
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            hideModal(modal);
        }
    });
    
    return modal;
}

function getAlertIcon(type) {
    const icons = {
        success: 'check-circle',
        danger: 'exclamation-triangle',
        warning: 'exclamation-circle',
        info: 'info-circle'
    };
    return icons[type] || 'info-circle';
}

/* ===== FORMULÁRIOS RESPONSIVOS ===== */
function initializeForms() {
    // Validação em tempo real
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        const inputs = form.querySelectorAll('input, select, textarea');
        
        inputs.forEach(input => {
            input.addEventListener('blur', function() {
                validateField(this);
            });
            
            input.addEventListener('input', function() {
                if (this.classList.contains('is-invalid')) {
                    validateField(this);
                }
            });
        });
        
        form.addEventListener('submit', function(e) {
            let isValid = true;
            
            inputs.forEach(input => {
                if (!validateField(input)) {
                    isValid = false;
                }
            });
            
            if (!isValid) {
                e.preventDefault();
                showAlert('Por favor, corrija os erros no formulário.', 'danger');
            }
        });
    });
    
    // Auto-resize para textareas
    const textareas = document.querySelectorAll('textarea');
    textareas.forEach(textarea => {
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = this.scrollHeight + 'px';
        });
    });
    
    // Máscaras para inputs
    initializeInputMasks();
}

function validateField(field) {
    const value = field.value.trim();
    let isValid = true;
    let message = '';
    
    // Remover classes anteriores
    field.classList.remove('is-valid', 'is-invalid');
    
    // Verificar se é obrigatório
    if (field.hasAttribute('required') && !value) {
        isValid = false;
        message = 'Este campo é obrigatório.';
    }
    
    // Validações específicas por tipo
    if (value && field.type === 'email') {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(value)) {
            isValid = false;
            message = 'Digite um e-mail válido.';
        }
    }
    
    if (value && field.type === 'tel') {
        const phoneRegex = /^\(\d{2}\)\s\d{4,5}-\d{4}$/;
        if (!phoneRegex.test(value)) {
            isValid = false;
            message = 'Digite um telefone válido.';
        }
    }
    
    if (value && field.type === 'password' && field.hasAttribute('data-min-length')) {
        const minLength = parseInt(field.getAttribute('data-min-length'));
        if (value.length < minLength) {
            isValid = false;
            message = `A senha deve ter pelo menos ${minLength} caracteres.`;
        }
    }
    
    // Aplicar classes e mensagens
    field.classList.add(isValid ? 'is-valid' : 'is-invalid');
    
    // Mostrar/ocultar mensagem de erro
    let feedback = field.parentNode.querySelector('.invalid-feedback');
    if (!isValid) {
        if (!feedback) {
            feedback = document.createElement('div');
            feedback.className = 'invalid-feedback';
            field.parentNode.appendChild(feedback);
        }
        feedback.textContent = message;
    } else if (feedback) {
        feedback.remove();
    }
    
    return isValid;
}

function initializeInputMasks() {
    // Máscara para telefone
    const phoneInputs = document.querySelectorAll('input[type="tel"]');
    phoneInputs.forEach(input => {
        input.addEventListener('input', function() {
            let value = this.value.replace(/\D/g, '');
            if (value.length <= 11) {
                value = value.replace(/(\d{2})(\d{4,5})(\d{4})/, '($1) $2-$3');
            }
            this.value = value;
        });
    });
    
    // Máscara para CPF
    const cpfInputs = document.querySelectorAll('input[data-mask="cpf"]');
    cpfInputs.forEach(input => {
        input.addEventListener('input', function() {
            let value = this.value.replace(/\D/g, '');
            value = value.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
            this.value = value;
        });
    });
    
    // Máscara para CNPJ
    const cnpjInputs = document.querySelectorAll('input[data-mask="cnpj"]');
    cnpjInputs.forEach(input => {
        input.addEventListener('input', function() {
            let value = this.value.replace(/\D/g, '');
            value = value.replace(/(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/, '$1.$2.$3/$4-$5');
            this.value = value;
        });
    });
    
    // Máscara para CEP
    const cepInputs = document.querySelectorAll('input[data-mask="cep"]');
    cepInputs.forEach(input => {
        input.addEventListener('input', function() {
            let value = this.value.replace(/\D/g, '');
            value = value.replace(/(\d{5})(\d{3})/, '$1-$2');
            this.value = value;
        });
    });
}

/* ===== TOOLTIPS ===== */
function initializeTooltips() {
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    
    tooltipElements.forEach(element => {
        element.addEventListener('mouseenter', showTooltip);
        element.addEventListener('mouseleave', hideTooltip);
        element.addEventListener('focus', showTooltip);
        element.addEventListener('blur', hideTooltip);
    });
}

function showTooltip(e) {
    const element = e.target;
    const text = element.getAttribute('data-tooltip');
    
    if (!text) return;
    
    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip';
    tooltip.textContent = text;
    tooltip.style.cssText = `
        position: absolute;
        background: #333;
        color: white;
        padding: 8px 12px;
        border-radius: 6px;
        font-size: 0.8rem;
        z-index: 1000;
        pointer-events: none;
        opacity: 0;
        transition: opacity 0.3s ease;
    `;
    
    document.body.appendChild(tooltip);
    
    // Posicionar tooltip
    const rect = element.getBoundingClientRect();
    tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
    tooltip.style.top = rect.top - tooltip.offsetHeight - 8 + 'px';
    
    // Mostrar tooltip
    setTimeout(() => {
        tooltip.style.opacity = '1';
    }, 10);
    
    element._tooltip = tooltip;
}

function hideTooltip(e) {
    const element = e.target;
    if (element._tooltip) {
        element._tooltip.remove();
        delete element._tooltip;
    }
}

/* ===== TABELAS RESPONSIVAS ===== */
function initializeTables() {
    updateResponsiveTables();
}

function updateResponsiveTables() {
    const tables = document.querySelectorAll('.table');
    
    tables.forEach(table => {
        if (!table.parentNode.classList.contains('table-responsive')) {
            const wrapper = document.createElement('div');
            wrapper.className = 'table-responsive';
            table.parentNode.insertBefore(wrapper, table);
            wrapper.appendChild(table);
        }
        
        // Adicionar indicadores de scroll em mobile
        if (window.innerWidth < 768) {
            addScrollIndicators(table.parentNode);
        }
    });
}

function addScrollIndicators(container) {
    const table = container.querySelector('.table');
    if (!table) return;
    
    const leftIndicator = document.createElement('div');
    const rightIndicator = document.createElement('div');
    
    leftIndicator.className = 'scroll-indicator left';
    rightIndicator.className = 'scroll-indicator right';
    
    leftIndicator.style.cssText = `
        position: absolute;
        left: 0;
        top: 0;
        bottom: 0;
        width: 20px;
        background: linear-gradient(to right, rgba(0,0,0,0.1), transparent);
        pointer-events: none;
        opacity: 0;
        transition: opacity 0.3s ease;
    `;
    
    rightIndicator.style.cssText = `
        position: absolute;
        right: 0;
        top: 0;
        bottom: 0;
        width: 20px;
        background: linear-gradient(to left, rgba(0,0,0,0.1), transparent);
        pointer-events: none;
        opacity: 1;
        transition: opacity 0.3s ease;
    `;
    
    container.style.position = 'relative';
    container.appendChild(leftIndicator);
    container.appendChild(rightIndicator);
    
    container.addEventListener('scroll', function() {
        const scrollLeft = this.scrollLeft;
        const scrollWidth = this.scrollWidth;
        const clientWidth = this.clientWidth;
        
        leftIndicator.style.opacity = scrollLeft > 0 ? '1' : '0';
        rightIndicator.style.opacity = scrollLeft < scrollWidth - clientWidth ? '1' : '0';
    });
}

/* ===== GRÁFICOS RESPONSIVOS ===== */
function initializeCharts() {
    // Configuração global para Chart.js
    if (window.Chart) {
        Chart.defaults.responsive = true;
        Chart.defaults.maintainAspectRatio = false;
        Chart.defaults.plugins.legend.labels.usePointStyle = true;
        Chart.defaults.plugins.legend.labels.padding = 20;
    }
}

/* ===== PWA (Progressive Web App) ===== */
function initializePWA() {
    // Registrar Service Worker
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/static/js/sw.js')
            .then(registration => {
                console.log('Service Worker registrado:', registration);
            })
            .catch(error => {
                console.log('Erro ao registrar Service Worker:', error);
            });
    }
    
    // Prompt para instalar PWA
    let deferredPrompt;
    
    window.addEventListener('beforeinstallprompt', (e) => {
        e.preventDefault();
        deferredPrompt = e;
        
        // Mostrar botão de instalação
        const installButton = document.createElement('button');
        installButton.className = 'btn btn-primary install-pwa';
        installButton.innerHTML = '<i class="fas fa-download"></i> Instalar App';
        installButton.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 1000;
            border-radius: 50px;
            padding: 12px 20px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        `;
        
        installButton.addEventListener('click', () => {
            deferredPrompt.prompt();
            deferredPrompt.userChoice.then((choiceResult) => {
                if (choiceResult.outcome === 'accepted') {
                    console.log('PWA instalado');
                }
                deferredPrompt = null;
                installButton.remove();
            });
        });
        
        document.body.appendChild(installButton);
        
        // Remover botão após 10 segundos se não clicado
        setTimeout(() => {
            if (installButton.parentNode) {
                installButton.remove();
            }
        }, 10000);
    });
}

/* ===== UTILITÁRIOS ===== */

// Debounce function
function debounce(func, wait, immediate) {
    let timeout;
    return function executedFunction() {
        const context = this;
        const args = arguments;
        const later = function() {
            timeout = null;
            if (!immediate) func.apply(context, args);
        };
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func.apply(context, args);
    };
}

// Throttle function
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Smooth scroll
function smoothScrollTo(target, duration = 1000) {
    const targetElement = typeof target === 'string' ? document.querySelector(target) : target;
    if (!targetElement) return;
    
    const targetPosition = targetElement.getBoundingClientRect().top + window.pageYOffset;
    const startPosition = window.pageYOffset;
    const distance = targetPosition - startPosition;
    let startTime = null;
    
    function animation(currentTime) {
        if (startTime === null) startTime = currentTime;
        const timeElapsed = currentTime - startTime;
        const run = ease(timeElapsed, startPosition, distance, duration);
        window.scrollTo(0, run);
        if (timeElapsed < duration) requestAnimationFrame(animation);
    }
    
    function ease(t, b, c, d) {
        t /= d / 2;
        if (t < 1) return c / 2 * t * t + b;
        t--;
        return -c / 2 * (t * (t - 2) - 1) + b;
    }
    
    requestAnimationFrame(animation);
}

// Lazy loading para imagens
function initializeLazyLoading() {
    const images = document.querySelectorAll('img[data-src]');
    
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.remove('lazy');
                imageObserver.unobserve(img);
            }
        });
    });
    
    images.forEach(img => imageObserver.observe(img));
}

// Inicializar lazy loading quando disponível
if (window.IntersectionObserver) {
    initializeLazyLoading();
}

/* ===== EXPORTAR FUNÇÕES GLOBAIS ===== */
window.ResponsiveUtils = {
    showModal: showModal,
    hideModal: hideModal,
    confirmAction: window.confirmAction,
    showAlert: window.showAlert,
    smoothScrollTo,
    debounce,
    throttle
};