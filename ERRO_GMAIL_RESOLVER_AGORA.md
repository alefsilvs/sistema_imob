# 🚨 ERRO GMAIL: Username and Password not accepted

## ❌ ERRO IDENTIFICADO
```
Erro: (535, b'5.7.8 Username and Password not accepted. 
For more information, go to https://support.google.com/mail/?p=BadCredentials')
```

## 🔍 CAUSA DO PROBLEMA
Você ainda está usando configurações de exemplo no arquivo `.env`:
- `EMAIL_HOST_USER=seu-email@gmail.com`
- `EMAIL_HOST_PASSWORD=sua-senha-de-app-do-gmail`

## ✅ SOLUÇÃO PASSO A PASSO

### PASSO 1: Configure sua conta Gmail

1. **Acesse**: https://myaccount.google.com/security
2. **Ative a Verificação em duas etapas** (obrigatório)
3. **Vá em "Senhas de app"** (App passwords)
4. **Selecione "Email"** como aplicativo
5. **Copie a senha de 16 caracteres** (ex: `abcd efgh ijkl mnop`)

### PASSO 2: Edite o arquivo .env

**Substitua estas linhas no arquivo `.env`:**

```env
# ANTES (valores de exemplo):
EMAIL_HOST_USER=seu-email@gmail.com
EMAIL_HOST_PASSWORD=sua-senha-de-app-do-gmail
DEFAULT_FROM_EMAIL=seu-email@gmail.com

# DEPOIS (seus valores REAIS):
EMAIL_HOST_USER=seuemail@gmail.com
EMAIL_HOST_PASSWORD=abcd efgh ijkl mnop
DEFAULT_FROM_EMAIL=seuemail@gmail.com
```

### PASSO 3: Reinicie o servidor

1. **No terminal do Django**, pressione `Ctrl+C`
2. **Execute**: `python manage.py runserver`

### PASSO 4: Teste imediatamente

**Execute**: `python testar_email.py`

## 🔧 EXEMPLO REAL DE CONFIGURAÇÃO

```env
# Se seu email for: joao.silva@gmail.com
# E sua senha de app for: abcd efgh ijkl mnop

EMAIL_HOST_USER=joao.silva@gmail.com
EMAIL_HOST_PASSWORD=abcd efgh ijkl mnop
DEFAULT_FROM_EMAIL=joao.silva@gmail.com
```

## ⚠️ PONTOS IMPORTANTES

- **NUNCA** use sua senha normal do Gmail
- **SEMPRE** use a senha de app de 16 caracteres
- **MANTENHA** os espaços na senha de app (ex: `abcd efgh ijkl mnop`)
- **CERTIFIQUE-SE** de que a verificação em 2 etapas está ativa

## 🆘 SE AINDA NÃO FUNCIONAR

### Verifique se:
1. ✅ Verificação em 2 etapas está ATIVA
2. ✅ Senha de app foi gerada CORRETAMENTE
3. ✅ Email está digitado SEM ERROS
4. ✅ Senha de app foi copiada COMPLETA (16 caracteres)
5. ✅ Servidor Django foi REINICIADO

### Links úteis:
- **Senhas de app**: https://myaccount.google.com/apppasswords
- **Verificação em 2 etapas**: https://myaccount.google.com/signinoptions/two-step-verification
- **Suporte Google**: https://support.google.com/mail/?p=BadCredentials

---

**🔥 AÇÃO URGENTE: Configure suas credenciais REAIS agora!**