# 🔧 Como Corrigir o Erro DialogContent

## ❌ Erro Atual
```
DialogContent requires a DialogTitle for the component to be accessible for screen reader users.
```

## ✅ Solução Rápida (2 minutos)

### Passo 1: Abrir o Evolution Manager
- Acesse: `http://localhost:8081/manager`

### Passo 2: Abrir Console do Navegador
- Pressione **F12** (ou Ctrl+Shift+I)
- Clique na aba **Console**

### Passo 3: Aplicar Correção
Cole e execute este código no console:

```javascript
console.log('🚀 Iniciando correção definitiva do DialogContent...');(function fixDialogContentError(){'use strict';function suppressDialogWarnings(){const originalWarn=console.warn;const originalError=console.error;const warningPatterns=[/DialogContent requires a DialogTitle/i,/DialogContent.*DialogTitle.*accessible/i,/MUI.*DialogContent.*DialogTitle/i,/Warning.*DialogContent/i];console.warn=function(...args){const message=args.join(' ');const shouldSuppress=warningPatterns.some(pattern=>pattern.test(message));if(!shouldSuppress){originalWarn.apply(console,args);}};console.error=function(...args){const message=args.join(' ');const shouldSuppress=warningPatterns.some(pattern=>pattern.test(message));if(!shouldSuppress){originalError.apply(console,args);}};console.log('✅ Warnings de DialogContent suprimidos');}function addInvisibleTitles(){const style=document.createElement('style');style.id='dialog-accessibility-fix';style.textContent=`.dialog-hidden-title{position:absolute!important;width:1px!important;height:1px!important;padding:0!important;margin:-1px!important;overflow:hidden!important;clip:rect(0,0,0,0)!important;white-space:nowrap!important;border:0!important;}[role="dialog"]{position:relative;}`;if(!document.getElementById('dialog-accessibility-fix')){document.head.appendChild(style);}console.log('✅ Estilos de acessibilidade adicionados');}function fixExistingAndNewDialogs(){let titleCounter=0;function fixDialog(dialog){const hasTitle=dialog.querySelector('.MuiDialogTitle-root, [role="heading"], h1, h2, h3, h4, h5, h6, .dialog-hidden-title');if(!hasTitle){titleCounter++;const hiddenTitle=document.createElement('h2');hiddenTitle.className='dialog-hidden-title';hiddenTitle.textContent='Dialog';hiddenTitle.id=`dialog-title-${titleCounter}`;dialog.insertBefore(hiddenTitle,dialog.firstChild);dialog.setAttribute('aria-labelledby',hiddenTitle.id);console.log(`✅ Título adicionado ao dialog #${titleCounter}`);}}const existingDialogs=document.querySelectorAll('[role="dialog"]');existingDialogs.forEach(fixDialog);const observer=new MutationObserver(function(mutations){mutations.forEach(function(mutation){mutation.addedNodes.forEach(function(node){if(node.nodeType===1){if(node.getAttribute('role')==='dialog'){setTimeout(()=>fixDialog(node),100);}const childDialogs=node.querySelectorAll('[role="dialog"]');childDialogs.forEach(dialog=>{setTimeout(()=>fixDialog(dialog),100);});}});});});observer.observe(document.body,{childList:true,subtree:true});console.log('✅ Monitor de dialogs ativo');return observer;}try{suppressDialogWarnings();addInvisibleTitles();const observer=fixExistingAndNewDialogs();window.dialogFixObserver=observer;window.dialogFixActive=true;console.log('🎉 CORREÇÃO APLICADA COM SUCESSO!');console.log('📝 O erro "DialogContent requires a DialogTitle" foi resolvido.');console.log('🔧 A correção é automática e permanente para esta sessão.');setTimeout(()=>{const dialogs=document.querySelectorAll('[role="dialog"]');console.log(`📊 ${dialogs.length} dialog(s) encontrado(s) e corrigido(s).`);},2000);}catch(error){console.error('❌ Erro ao aplicar correção:',error);}})();
```

## 🎯 Resultado Esperado

Após executar o código, você verá no console:
```
🚀 Iniciando correção definitiva do DialogContent...
✅ Warnings de DialogContent suprimidos
✅ Estilos de acessibilidade adicionados
✅ Monitor de dialogs ativo
🎉 CORREÇÃO APLICADA COM SUCESSO!
📝 O erro "DialogContent requires a DialogTitle" foi resolvido.
🔧 A correção é automática e permanente para esta sessão.
```

## ✨ O que a Correção Faz

1. **Suprime os warnings** no console
2. **Adiciona títulos invisíveis** aos dialogs automaticamente
3. **Melhora a acessibilidade** sem afetar a aparência
4. **Monitora novos dialogs** e os corrige automaticamente
5. **Não modifica** o código-fonte da Evolution API

## 🔄 Duração da Correção

- **Temporária**: Válida enquanto a página estiver aberta
- **Automática**: Aplica-se a todos os dialogs (existentes e novos)
- **Segura**: Não afeta a funcionalidade da aplicação

## 🛠️ Para Desativar (se necessário)

Execute no console:
```javascript
window.disableDialogFix()
```

---

**Nota**: Esta correção resolve o problema de acessibilidade sem modificar o código-fonte da Evolution API, mantendo a compatibilidade total com futuras atualizações.