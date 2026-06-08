/**
 * Sistema de Edição Inline para Elementos A e DIV
 * Permite editar elementos diretamente na página
 */

class EditableElements {
    constructor() {
        this.isEditMode = false;
        this.originalContent = new Map();
        this.editableElements = [];
        this.init();
    }

    init() {
        this.createEditButton();
        this.setupEventListeners();
        console.log('Sistema de edição inline inicializado');
    }

    setupEventListeners() {
        // Configurar event listeners globais
        document.addEventListener('keydown', (event) => {
            // Esc para sair do modo de edição
            if (event.key === 'Escape' && this.isEditMode) {
                this.toggleEditMode();
            }
        });

        // Prevenir navegação acidental durante edição
        window.addEventListener('beforeunload', (event) => {
            if (this.isEditMode) {
                event.preventDefault();
                event.returnValue = 'Você tem alterações não salvas. Deseja realmente sair?';
            }
        });
    }

    createEditButton() {
        // Criar botão de toggle para modo de edição
        const editButton = document.createElement('button');
        editButton.id = 'toggle-edit-mode';
        editButton.className = 'btn btn-primary position-fixed';
        editButton.style.cssText = `
            top: 20px;
            right: 20px;
            z-index: 9999;
            border-radius: 50px;
            padding: 10px 20px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        `;
        editButton.innerHTML = '<i class="bi bi-pencil"></i> Editar';
        editButton.title = 'Ativar/Desativar modo de edição';
        
        document.body.appendChild(editButton);
        
        editButton.addEventListener('click', () => this.toggleEditMode());
    }

    toggleEditMode() {
        this.isEditMode = !this.isEditMode;
        const button = document.getElementById('toggle-edit-mode');
        
        if (this.isEditMode) {
            this.enableEditMode();
            button.innerHTML = '<i class="bi bi-check"></i> Salvar';
            button.className = 'btn btn-success position-fixed';
            this.showNotification('Modo de edição ativado! Clique nos elementos para editá-los.', 'info');
            
            // Disparar evento para o assistente de IA
            document.dispatchEvent(new CustomEvent('editModeChanged', {
                detail: { isEditMode: true }
            }));
        } else {
            this.disableEditMode();
            button.innerHTML = '<i class="bi bi-pencil"></i> Editar';
            button.className = 'btn btn-primary position-fixed';
            this.saveChanges();
            
            // Disparar evento para o assistente de IA
            document.dispatchEvent(new CustomEvent('editModeChanged', {
                detail: { isEditMode: false }
            }));
        }
    }

    enableEditMode() {
        // Encontrar todos os elementos editáveis
        const editableSelectors = [
            'a:not([href*="javascript:"]):not([data-bs-toggle]):not([onclick])',
            'div.card-title',
            'div.card-text',
            'div.content-section',
            'div.editable',
            'header:not(.navbar):not(.fixed-top)',
            'main',
            'footer:not(.fixed-bottom)',
            'h1, h2, h3, h4, h5, h6',
            'p:not(.fixed)',
            'span.editable'
        ];

        editableSelectors.forEach(selector => {
            const elements = document.querySelectorAll(selector);
            elements.forEach(element => {
                if (!this.isSystemElement(element)) {
                    this.makeElementEditable(element);
                }
            });
        });
    }

    isSystemElement(element) {
        // Verificar se é um elemento do sistema que não deve ser editado
        const systemClasses = [
            'navbar', 'nav-link', 'dropdown', 'btn', 'form-control',
            'pagination', 'breadcrumb', 'alert', 'modal', 'tooltip',
            'fixed-top', 'fixed-bottom'
        ];
        
        const systemIds = ['toggle-edit-mode', 'loading-overlay'];
        
        if (systemIds.includes(element.id)) return true;
        
        // Verificar se o elemento tem classes do sistema ou está dentro de um elemento do sistema
        return systemClasses.some(cls => 
            element.classList.contains(cls) || 
            element.closest(`.${cls}`)
        );
    }

    makeElementEditable(element) {
        // Salvar conteúdo original
        const elementId = this.generateElementId(element);
        this.originalContent.set(elementId, element.innerHTML);
        
        // Adicionar atributos de edição
        element.contentEditable = true;
        element.classList.add('editable-active');
        element.dataset.editableId = elementId;
        
        // Adicionar estilos visuais
        element.style.cssText += `
            border: 2px dashed #007bff;
            padding: 5px;
            margin: 2px;
            border-radius: 4px;
            background-color: rgba(0, 123, 255, 0.05);
            transition: all 0.3s ease;
        `;
        
        // Adicionar eventos
        element.addEventListener('focus', this.onElementFocus.bind(this));
        element.addEventListener('blur', this.onElementBlur.bind(this));
        element.addEventListener('keydown', this.onElementKeydown.bind(this));
        element.addEventListener('click', () => {
            // Disparar evento para o assistente de IA
            document.dispatchEvent(new CustomEvent('elementSelected', {
                detail: { element: element }
            }));
        });
        
        this.editableElements.push(element);
    }

    generateElementId(element) {
        // Gerar ID único para o elemento
        if (element.id) return element.id;
        
        const tagName = element.tagName.toLowerCase();
        const className = element.className.replace(/\s+/g, '-');
        const textContent = element.textContent.substring(0, 20).replace(/\s+/g, '-');
        const timestamp = Date.now();
        
        return `${tagName}-${className}-${textContent}-${timestamp}`.replace(/[^a-zA-Z0-9-]/g, '');
    }

    onElementFocus(event) {
        const element = event.target;
        element.style.borderColor = '#28a745';
        element.style.backgroundColor = 'rgba(40, 167, 69, 0.1)';
        
        // Mostrar tooltip com instruções
        this.showTooltip(element, 'Editando... Pressione Enter para nova linha, Esc para cancelar');
    }

    onElementBlur(event) {
        const element = event.target;
        element.style.borderColor = '#007bff';
        element.style.backgroundColor = 'rgba(0, 123, 255, 0.05)';
        
        this.hideTooltip();
    }

    onElementKeydown(event) {
        if (event.key === 'Escape') {
            event.preventDefault();
            const element = event.target;
            const elementId = element.dataset.editableId;
            
            // Restaurar conteúdo original
            if (this.originalContent.has(elementId)) {
                element.innerHTML = this.originalContent.get(elementId);
            }
            
            element.blur();
        }
    }

    disableEditMode() {
        this.editableElements.forEach(element => {
            element.contentEditable = false;
            element.classList.remove('editable-active');
            element.style.border = '';
            element.style.padding = '';
            element.style.margin = '';
            element.style.borderRadius = '';
            element.style.backgroundColor = '';
            
            // Remover event listeners
            element.removeEventListener('focus', this.onElementFocus);
            element.removeEventListener('blur', this.onElementBlur);
            element.removeEventListener('keydown', this.onElementKeydown);
        });
        
        this.editableElements = [];
        this.hideTooltip();
    }

    saveChanges() {
        const changes = [];
        
        this.editableElements.forEach(element => {
            const elementId = element.dataset.editableId;
            const originalContent = this.originalContent.get(elementId);
            const currentContent = element.innerHTML;
            
            if (originalContent !== currentContent) {
                changes.push({
                    elementId: elementId,
                    selector: this.getElementSelector(element),
                    originalContent: originalContent,
                    newContent: currentContent,
                    tagName: element.tagName.toLowerCase()
                });
            }
        });
        
        if (changes.length > 0) {
            this.sendChangesToServer(changes);
            this.showNotification(`${changes.length} alterações salvas com sucesso!`, 'success');
        } else {
            this.showNotification('Nenhuma alteração detectada.', 'info');
        }
        
        this.originalContent.clear();
    }

    getElementSelector(element) {
        // Gerar seletor CSS para o elemento
        let selector = element.tagName.toLowerCase();
        
        if (element.id) {
            selector += `#${element.id}`;
        } else if (element.className) {
            const classes = element.className.split(' ')
                .filter(cls => cls && !cls.includes('editable'))
                .join('.');
            if (classes) {
                selector += `.${classes}`;
            }
        }
        
        return selector;
    }

    sendChangesToServer(changes) {
        // Enviar alterações para o servidor via AJAX
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
                         window.APP_CONFIG?.csrfToken;
        
        fetch('/api/save-editable-changes/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({
                changes: changes,
                page_url: window.location.pathname
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                console.log('Alterações salvas no servidor:', data);
            } else {
                console.error('Erro ao salvar alterações:', data.error);
                this.showNotification('Erro ao salvar alterações no servidor.', 'error');
            }
        })
        .catch(error => {
            console.error('Erro na requisição:', error);
            this.showNotification('Erro de conexão ao salvar alterações.', 'error');
        });
    }

    showTooltip(element, message) {
        this.hideTooltip();
        
        const tooltip = document.createElement('div');
        tooltip.id = 'edit-tooltip';
        tooltip.className = 'position-absolute bg-dark text-white p-2 rounded';
        tooltip.style.cssText = `
            z-index: 10000;
            font-size: 12px;
            max-width: 200px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        `;
        tooltip.textContent = message;
        
        const rect = element.getBoundingClientRect();
        tooltip.style.top = (rect.top - 40 + window.scrollY) + 'px';
        tooltip.style.left = (rect.left + window.scrollX) + 'px';
        
        document.body.appendChild(tooltip);
    }

    hideTooltip() {
        const tooltip = document.getElementById('edit-tooltip');
        if (tooltip) {
            tooltip.remove();
        }
    }

    showNotification(message, type = 'info') {
        // Usar função global se existir, senão criar própria
        if (typeof showNotification === 'function') {
            showNotification(message, type);
        } else {
            const notification = document.createElement('div');
            notification.className = `alert alert-${type === 'error' ? 'danger' : type} position-fixed`;
            notification.style.cssText = `
                top: 80px;
                right: 20px;
                z-index: 9999;
                max-width: 300px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            `;
            notification.textContent = message;
            
            document.body.appendChild(notification);
            
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.remove();
                }
            }, 4000);
        }
    }
}

// Inicializar quando DOM estiver pronto
document.addEventListener('DOMContentLoaded', function() {
    // Verificar se não estamos em páginas administrativas
    if (!window.location.pathname.includes('/admin/')) {
        window.editableElements = new EditableElements();
    }
});

// Exportar para uso global
window.EditableElements = EditableElements;