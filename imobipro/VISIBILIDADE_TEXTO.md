# Guia de Visibilidade de Texto - ImobiPro

## Problema Resolvido
Este guia documenta as melhorias implementadas para resolver problemas de visibilidade de texto em elementos `div` com texto branco ou com baixo contraste.

## Classes CSS Disponíveis

### 1. Classes de Texto Visível

#### `.text-visible`
Texto com contraste melhorado e sombra sutil.
```html
<div class="text-visible">Texto com melhor visibilidade</div>
```

#### `.text-visible-light`
Para uso em fundos escuros - texto claro com sombra forte.
```html
<div style="background: #333;" class="text-visible-light">Texto em fundo escuro</div>
```

#### `.text-visible-dark`
Para uso em fundos claros - texto escuro com sombra sutil.
```html
<div style="background: #f0f0f0;" class="text-visible-dark">Texto em fundo claro</div>
```

### 2. Classes de Fundo e Contraste

#### `.bg-contrast`
Fundo com gradiente sutil e efeito blur para melhor legibilidade.
```html
<div class="bg-contrast">
    <p>Conteúdo com fundo contrastante</p>
</div>
```

#### `.text-readable`
Texto com fundo semi-transparente para garantir legibilidade.
```html
<div style="background-image: url('imagem.jpg');">
    <span class="text-readable">Texto legível sobre imagem</span>
</div>
```

### 3. Classes Específicas para Texto Branco

#### `.white-text-improved`
Texto branco com sombra melhorada e peso de fonte aumentado.
```html
<div style="background: linear-gradient(135deg, #333, #666);">
    <h3 class="white-text-improved">Título com texto branco melhorado</h3>
</div>
```

#### `.dark-bg-text`
Texto com fundo escuro semi-transparente.
```html
<div class="dark-bg-text">Texto com fundo escuro automático</div>
```

#### `.text-outline`
Texto com contorno para melhor definição.
```html
<h2 class="text-outline" style="color: white;">Texto com contorno</h2>
```

## Correções Automáticas

O CSS agora inclui correções automáticas para:

1. **Divs com texto branco inline**: Automaticamente adiciona sombra e peso de fonte
2. **Texto branco em fundos claros**: Converte automaticamente para texto escuro
3. **Elementos com estilos inline problemáticos**: Aplica melhorias de contraste

## Exemplos Práticos

### Antes (Problemático)
```html
<div style="background: white; color: white; padding: 20px;">
    Texto invisível
</div>
```

### Depois (Corrigido Automaticamente)
```html
<div style="background: white; color: white; padding: 20px;">
    Texto agora visível (corrigido pelo CSS)
</div>
```

### Melhor Prática
```html
<div style="background: white; padding: 20px;">
    <span class="text-visible">Texto com visibilidade otimizada</span>
</div>
```

## Variáveis CSS Disponíveis

```css
--text-contrast: #1f2937;        /* Cor de texto com alto contraste */
--text-light-bg: #374151;        /* Texto para fundos claros */
--text-dark-bg: #f9fafb;         /* Texto para fundos escuros */
--shadow-text: 0 1px 3px rgba(0, 0, 0, 0.3); /* Sombra padrão */
```

## Recomendações

1. **Use as classes utilitárias** em vez de estilos inline quando possível
2. **Teste a visibilidade** em diferentes dispositivos e condições de luz
3. **Combine classes** para obter o melhor resultado (ex: `text-visible bg-contrast`)
4. **Evite texto branco em fundos claros** - o CSS corrige automaticamente, mas é melhor prevenir

## Suporte a Acessibilidade

Todas as melhorias seguem as diretrizes WCAG 2.1 para contraste de cores:
- Contraste mínimo de 4.5:1 para texto normal
- Contraste mínimo de 3:1 para texto grande
- Suporte a leitores de tela mantido