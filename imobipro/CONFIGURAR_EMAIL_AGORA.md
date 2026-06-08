# 🚨 CONFIGURAÇÃO URGENTE DE EMAIL

## ❌ PROBLEMA IDENTIFICADO
Os emails não estão chegando porque você ainda está usando configurações de exemplo!

## ✅ SOLUÇÃO RÁPIDA

### PASSO 1: Escolha seu provedor de email

#### 📧 GMAIL (Recomendado)
1. Acesse: https://myaccount.google.com/security
2. Ative a **Verificação em duas etapas**
3. Vá em **Senhas de app**
4. Gere uma senha de app para "Email"
5. Copie a senha de 16 caracteres (ex: `abcd efgh ijkl mnop`)

#### 📧 OUTLOOK/HOTMAIL
1. Acesse: https://account.live.com/proofs/manage
2. Ative a **Verificação em duas etapas**
3. Gere uma **senha de app**
4. Copie a senha gerada

### PASSO 2: Edite o arquivo .env

Abra o arquivo `.env` e substitua estas linhas:

```env
# ANTES (valores de exemplo):
EMAIL_HOST_USER=seu-email@gmail.com
EMAIL_HOST_PASSWORD=sua-senha-de-app-do-gmail
DEFAULT_FROM_EMAIL=seu-email@gmail.com

# DEPOIS (seus valores reais):
EMAIL_HOST_USER=seuemail@gmail.com
EMAIL_HOST_PASSWORD=abcd efgh ijkl mnop
DEFAULT_FROM_EMAIL=seuemail@gmail.com
```

### PASSO 3: Reinicie o servidor

1. No terminal do Django, pressione `Ctrl+C`
2. Execute: `python manage.py runserver`

### PASSO 4: Teste o email

Execute: `python testar_email.py`

## 🔧 CONFIGURAÇÕES PARA OUTROS PROVEDORES

### Yahoo Mail
```env
EMAIL_HOST_USER=seuemail@yahoo.com
EMAIL_HOST_PASSWORD=sua-senha-de-app
DEFAULT_FROM_EMAIL=seuemail@yahoo.com
```

### Servidor SMTP personalizado
Edite também o `settings.py`:
```python
EMAIL_HOST = 'smtp.seuservidor.com'
EMAIL_PORT = 587  # ou 465 para SSL
EMAIL_USE_TLS = True  # ou False para SSL
```

## ⚠️ IMPORTANTE

- **NUNCA** use sua senha normal do email
- **SEMPRE** use senha de app (16 caracteres)
- **MANTENHA** a autenticação de 2 fatores ativada
- **TESTE** após cada configuração

## 🆘 PROBLEMAS COMUNS

### "Authentication Required"
- Verifique se a senha de app está correta
- Confirme se a autenticação de 2 fatores está ativa

### "Connection refused"
- Verifique sua conexão com a internet
- Confirme se o EMAIL_HOST está correto

### "Invalid email"
- Verifique se o email está digitado corretamente
- Confirme se o email existe e está ativo

---

**📞 Após configurar, teste imediatamente com `python testar_email.py`**