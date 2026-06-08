/**
 * Sistema de Inteligência Artificial para Suporte aos Elementos Editáveis
 * Fornece sugestões inteligentes e ajuda contextual durante a edição
 */

class AIAssistant {
    constructor() {
        this.isActive = false;
        this.suggestions = [];
        this.contextHistory = [];
        this.init();
    }

    init() {
        this.createAIInterface();
        this.setupEventListeners();
        this.loadKnowledgeBase();
        console.log('Assistente de IA inicializado');
    }

    createAIInterface() {
        // Criar botão do assistente de IA
        const aiButton = document.createElement('button');
        aiButton.id = 'ai-assistant-toggle';
        aiButton.className = 'btn btn-info position-fixed';
        aiButton.style.cssText = `
            top: 80px;
            right: 20px;
            z-index: 9998;
            border-radius: 50px;
            padding: 10px 15px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            display: none;
        `;
        aiButton.innerHTML = '<i class="bi bi-robot"></i> IA';
        aiButton.title = 'Assistente de IA para Edição';
        
        document.body.appendChild(aiButton);

        // Criar painel do assistente
        this.createAIPanel();
        
        aiButton.addEventListener('click', () => this.toggleAI());
    }

    createAIPanel() {
        const aiPanel = document.createElement('div');
        aiPanel.id = 'ai-assistant-panel';
        aiPanel.className = 'position-fixed bg-white border rounded shadow-lg';
        aiPanel.style.cssText = `
            top: 130px;
            right: 20px;
            width: 350px;
            max-height: 500px;
            z-index: 9997;
            display: none;
            overflow-y: auto;
        `;

        aiPanel.innerHTML = `
            <div class="p-3 border-bottom bg-primary text-white">
                <h6 class="mb-0">
                    <i class="bi bi-robot me-2"></i>
                    Assistente de IA
                    <button class="btn btn-sm btn-outline-light float-end" onclick="window.aiAssistant.toggleAI()">
                        <i class="bi bi-x"></i>
                    </button>
                </h6>
            </div>
            <div class="p-3">
                <div id="ai-suggestions" class="mb-3">
                    <h6>Sugestões Inteligentes:</h6>
                    <div id="suggestions-list" class="text-muted">
                        Ative o modo de edição para receber sugestões...
                    </div>
                </div>
                <div id="ai-help" class="mb-3">
                    <h6>Ajuda Contextual:</h6>
                    <div id="help-content" class="small text-muted">
                        Clique em um elemento para receber ajuda específica.
                    </div>
                </div>
                <div id="ai-actions">
                    <button class="btn btn-sm btn-outline-primary me-2" onclick="window.aiAssistant.generateContent()">
                        <i class="bi bi-magic"></i> Gerar Conteúdo
                    </button>
                    <button class="btn btn-sm btn-outline-success" onclick="window.aiAssistant.optimizeContent()">
                        <i class="bi bi-speedometer2"></i> Otimizar
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(aiPanel);
    }

    setupEventListeners() {
        // Escutar eventos do sistema de edição
        document.addEventListener('editModeChanged', (e) => {
            this.onEditModeChanged(e.detail.isEditMode);
        });

        document.addEventListener('elementSelected', (e) => {
            this.onElementSelected(e.detail.element);
        });

        document.addEventListener('contentChanged', (e) => {
            this.onContentChanged(e.detail);
        });
    }

    loadKnowledgeBase() {
        // Base de conhecimento para sugestões
        this.knowledgeBase = {
            'a': {
                tips: [
                    'Use textos descritivos para links',
                    'Evite "clique aqui" - seja específico',
                    'Considere adicionar title para acessibilidade'
                ],
                suggestions: [
                    'Saiba mais sobre nossos serviços',
                    'Entre em contato conosco',
                    'Veja nosso portfólio completo'
                ]
            },
            'div': {
                tips: [
                    'Mantenha o conteúdo conciso e claro',
                    'Use hierarquia visual adequada',
                    'Considere o impacto no SEO'
                ],
                suggestions: [
                    'Bem-vindo ao nosso sistema',
                    'Descubra nossas funcionalidades',
                    'Gerencie seus imóveis com facilidade'
                ]
            },
            'header': {
                tips: [
                    'O cabeçalho deve ser impactante',
                    'Inclua informações essenciais',
                    'Mantenha consistência visual'
                ],
                suggestions: [
                    'Sistema Imobiliário Completo',
                    'Gestão Inteligente de Imóveis',
                    'Sua Imobiliária Digital'
                ]
            },
            'main': {
                tips: [
                    'Conteúdo principal deve ser relevante',
                    'Organize informações por prioridade',
                    'Use chamadas para ação claras'
                ],
                suggestions: [
                    'Gerencie todos os seus imóveis em um só lugar',
                    'Controle completo de contratos e inquilinos',
                    'Relatórios financeiros detalhados'
                ]
            },
            'footer': {
                tips: [
                    'Inclua informações de contato',
                    'Adicione links importantes',
                    'Mantenha informações atualizadas'
                ],
                suggestions: [
                    '© 2024 Sistema Imobiliário - Todos os direitos reservados',
                    'Desenvolvido com tecnologia avançada',
                    'Suporte técnico disponível 24/7'
                ]
            }
        };
    }

    toggleAI() {
        this.isActive = !this.isActive;
        const panel = document.getElementById('ai-assistant-panel');
        const button = document.getElementById('ai-assistant-toggle');
        
        if (this.isActive) {
            panel.style.display = 'block';
            button.innerHTML = '<i class="bi bi-robot"></i> IA ✓';
            this.updateSuggestions();
        } else {
            panel.style.display = 'none';
            button.innerHTML = '<i class="bi bi-robot"></i> IA';
        }
    }

    onEditModeChanged(isEditMode) {
        const aiButton = document.getElementById('ai-assistant-toggle');
        if (isEditMode) {
            aiButton.style.display = 'block';
            this.updateSuggestions('Modo de edição ativado! Clique em elementos para receber sugestões específicas.');
        } else {
            aiButton.style.display = 'none';
            if (this.isActive) {
                this.toggleAI();
            }
        }
    }

    onElementSelected(element) {
        if (!this.isActive) return;

        const tagName = element.tagName.toLowerCase();
        const knowledge = this.knowledgeBase[tagName];
        
        if (knowledge) {
            this.showElementHelp(element, knowledge);
            this.generateSmartSuggestions(element, knowledge);
        }
    }

    onContentChanged(detail) {
        if (!this.isActive) return;
        
        this.contextHistory.push({
            element: detail.element,
            oldContent: detail.oldContent,
            newContent: detail.newContent,
            timestamp: new Date()
        });

        this.analyzeContentQuality(detail.newContent, detail.element);
    }

    showElementHelp(element, knowledge) {
        const helpContent = document.getElementById('help-content');
        const tagName = element.tagName.toLowerCase();
        
        let helpHTML = `
            <div class="alert alert-info p-2 mb-2">
                <strong>Editando: &lt;${tagName}&gt;</strong>
            </div>
            <ul class="small mb-0">
        `;
        
        knowledge.tips.forEach(tip => {
            helpHTML += `<li>${tip}</li>`;
        });
        
        helpHTML += '</ul>';
        helpContent.innerHTML = helpHTML;
    }

    generateSmartSuggestions(element, knowledge) {
        const suggestionsList = document.getElementById('suggestions-list');
        const currentContent = element.textContent.trim();
        
        let suggestionsHTML = '<div class="small">';
        
        if (currentContent.length < 10) {
            suggestionsHTML += '<div class="alert alert-warning p-2 mb-2">Conteúdo muito curto. Considere expandir.</div>';
        }
        
        suggestionsHTML += '<strong>Sugestões de conteúdo:</strong><ul>';
        
        knowledge.suggestions.forEach(suggestion => {
            suggestionsHTML += `
                <li>
                    <a href="#" class="text-decoration-none" onclick="window.aiAssistant.applySuggestion('${suggestion}', event)">
                        ${suggestion}
                    </a>
                </li>
            `;
        });
        
        suggestionsHTML += '</ul></div>';
        suggestionsList.innerHTML = suggestionsHTML;
    }

    applySuggestion(suggestion, event) {
        event.preventDefault();
        
        // Encontrar elemento atualmente selecionado
        const activeElement = document.querySelector('.editable-active');
        if (activeElement) {
            activeElement.textContent = suggestion;
            
            // Disparar evento de mudança
            const changeEvent = new CustomEvent('contentChanged', {
                detail: {
                    element: activeElement,
                    oldContent: activeElement.textContent,
                    newContent: suggestion
                }
            });
            document.dispatchEvent(changeEvent);
            
            this.showNotification('Sugestão aplicada com sucesso!', 'success');
        }
    }

    generateContent() {
        const activeElement = document.querySelector('.editable-active');
        if (!activeElement) {
            this.showNotification('Selecione um elemento primeiro', 'warning');
            return;
        }

        const tagName = activeElement.tagName.toLowerCase();
        const knowledge = this.knowledgeBase[tagName];
        
        if (knowledge && knowledge.suggestions.length > 0) {
            const randomSuggestion = knowledge.suggestions[Math.floor(Math.random() * knowledge.suggestions.length)];
            activeElement.textContent = randomSuggestion;
            this.showNotification('Conteúdo gerado automaticamente!', 'success');
        }
    }

    optimizeContent() {
        const activeElement = document.querySelector('.editable-active');
        if (!activeElement) {
            this.showNotification('Selecione um elemento primeiro', 'warning');
            return;
        }

        let content = activeElement.textContent.trim();
        
        // Otimizações básicas
        content = content.replace(/\s+/g, ' '); // Remover espaços extras
        content = content.charAt(0).toUpperCase() + content.slice(1); // Primeira letra maiúscula
        
        // Remover pontuação desnecessária no final
        if (content.endsWith('...')) {
            content = content.slice(0, -3);
        }
        
        activeElement.textContent = content;
        this.showNotification('Conteúdo otimizado!', 'success');
    }

    analyzeContentQuality(content, element) {
        const issues = [];
        
        if (content.length < 5) {
            issues.push('Conteúdo muito curto');
        }
        
        if (content.length > 200) {
            issues.push('Conteúdo muito longo');
        }
        
        if (!/[.!?]$/.test(content) && element.tagName.toLowerCase() === 'p') {
            issues.push('Considere adicionar pontuação final');
        }
        
        if (issues.length > 0) {
            this.showNotification(`Sugestões: ${issues.join(', ')}`, 'info');
        }
    }

    updateSuggestions(message = null) {
        const suggestionsList = document.getElementById('suggestions-list');
        if (message) {
            suggestionsList.innerHTML = `<div class="text-info">${message}</div>`;
        }
    }

    showNotification(message, type = 'info') {
        // Usar função global se existir
        if (typeof showNotification === 'function') {
            showNotification(message, type);
        } else {
            console.log(`AI Assistant: ${message}`);
        }
    }
}

// Inicializar quando DOM estiver pronto
document.addEventListener('DOMContentLoaded', function() {
    if (!window.location.pathname.includes('/admin/')) {
        window.aiAssistant = new AIAssistant();
    }
});