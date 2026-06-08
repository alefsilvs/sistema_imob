# Como Gerar Senha de App do Gmail (16 Caracteres)

## ⚠️ IMPORTANTE
Esta senha de app é necessária para resolver o erro:
```
535, b'5.7.8 Username and Password not accepted'
```

## Pré-requisitos
1. **Verificação em 2 etapas DEVE estar ativada**
2. Conta Gmail válida

## Passo a Passo Completo

### 1. Ativar Verificação em 2 Etapas
1. Acesse: https://myaccount.google.com/security
2. Clique em "Verificação em duas etapas"
3. Siga as instruções para ativar
4. **AGUARDE 5-10 minutos** após ativar

### 2. Gerar Senha de App
1. Ainda em https://myaccount.google.com/security
2. Procure por "Senhas de app" (App passwords)
3. Clique em "Senhas de app"
4. Pode pedir para fazer login novamente
5. Selecione:
   - **App**: "Email"
   - **Dispositivo**: "Computador Windows" ou "Outro"
6. Digite um nome: "Sistema Imobiliário" ou "Django"
7. Clique em "Gerar"

### 3. Copiar a Senha Gerada
- O Google mostrará uma senha de **16 caracteres**
- Exemplo: `abcd efgh ijkl mnop`
- **COPIE EXATAMENTE** (com ou sem espaços)
- **GUARDE EM LOCAL SEGURO**

## Configurar no Sistema

### 1. Editar arquivo .env
```env
# Substitua pelos seus dados reais:
EMAIL_HOST_USER=seuemail@gmail.com
EMAIL_HOST_PASSWORD=abcdefghijklmnop
DEFAULT_FROM_EMAIL=seuemail@gmail.com
```

### 2. Exemplo Real
```env
# Se seu email for joao@gmail.com e a senha gerada for "abcd efgh ijkl mnop":
EMAIL_HOST_USER=joao@gmail.com
EMAIL_HOST_PASSWORD=abcdefghijklmnop
DEFAULT_FROM_EMAIL=joao@gmail.com
```

## ⚠️ PONTOS IMPORTANTES

1. **NÃO use sua senha normal do Gmail**
2. **Use APENAS a senha de app de 16 caracteres**
3. **Pode incluir ou remover espaços** da senha
4. **Verificação em 2 etapas é OBRIGATÓRIA**
5. **Aguarde alguns minutos** após gerar antes de testar

## Testar Configuração

1. Salve o arquivo `.env`
2. Reinicie o servidor Django:
   ```
   Ctrl+C (no terminal do Django)
   python manage.py runserver
   ```
3. Execute o teste:
   ```
   python testar_email.py
   ```

## Solução de Problemas

### Se ainda der erro 535:
1. Verifique se copiou a senha corretamente
2. Confirme que a verificação em 2 etapas está ativa
3. Aguarde 10-15 minutos e tente novamente
4. Gere uma nova senha de app se necessário

### Links Úteis
- Configurações de segurança: https://myaccount.google.com/security
- Senhas de app: https://myaccount.google.com/apppasswords
- Verificação em 2 etapas: https://myaccount.google.com/signinoptions/two-step-verification

## Exemplo de Senha de App Válida
```
Formato do Google: abcd efgh ijkl mnop
Para usar no .env: abcdefghijklmnop (sem espaços)
```

---

**Após configurar corretamente, o sistema enviará emails automaticamente para:**
- Notificações de vencimento
- Alertas de segurança
- Relatórios de backup
- Envio de NFe
- Relatórios financeiros