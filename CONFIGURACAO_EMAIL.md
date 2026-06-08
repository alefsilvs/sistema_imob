# Configuração de Email SMTP

## Problema Identificado

O sistema está apresentando erro ao enviar notificações por email:
```
Erro: (530, b'5.7.0 Authentication Required. For more information, go to\n5.7.0  https://support.google.com/accounts/troubleshooter/2402620. d2e1a72fcca58-772590e0519sm9490934b3a.84 - gsmtp', 'noreply@sistema.com')
```

Este erro indica que as credenciais SMTP não estão configuradas corretamente.

## Solução

### 1. Configuração para Gmail

#### Passo 1: Ativar Autenticação de 2 Fatores
1. Acesse sua conta Google
2. Vá em "Segurança"
3. Ative a "Verificação em duas etapas"

#### Passo 2: Gerar Senha de App
1. Na seção "Segurança", procure por "Senhas de app"
2. Selecione "Email" como aplicativo
3. Selecione "Outro" como dispositivo e digite "Sistema Imobiliário"
4. Copie a senha gerada (16 caracteres)

#### Passo 3: Configurar no .env
Edite o arquivo `.env` e substitua:
```env
EMAIL_HOST_USER=seu-email@gmail.com
EMAIL_HOST_PASSWORD=sua-senha-de-app-do-gmail
DEFAULT_FROM_EMAIL=seu-email@gmail.com
```

### 2. Configuração para Outlook/Hotmail

#### Configurações no .env:
```env
EMAIL_HOST_USER=seu-email@outlook.com
EMAIL_HOST_PASSWORD=sua-senha
DEFAULT_FROM_EMAIL=seu-email@outlook.com
```

### 3. Configuração para Outros Provedores

#### Yahoo Mail:
```env
EMAIL_HOST_USER=seu-email@yahoo.com
EMAIL_HOST_PASSWORD=sua-senha-de-app
DEFAULT_FROM_EMAIL=seu-email@yahoo.com
```

#### Provedor Personalizado:
Se usar outro provedor, você também precisará alterar as configurações SMTP no `settings.py`:
```python
EMAIL_HOST = 'smtp.seuprovedor.com'
EMAIL_PORT = 587  # ou 465 para SSL
EMAIL_USE_TLS = True  # ou EMAIL_USE_SSL = True
```

## Teste da Configuração

Após configurar as credenciais:

1. Reinicie o servidor Django:
   ```bash
   python manage.py runserver
   ```

2. Teste o envio de notificação:
   - Acesse o sistema
   - Vá em "Notificações" > "Enviar Notificação"
   - Selecione "Email" como canal
   - Envie uma notificação de teste

## Verificação de Problemas

### Erro 530 - Authentication Required
- Verifique se a senha de app está correta
- Confirme se a autenticação de 2 fatores está ativa
- Teste com uma nova senha de app

### Erro de Conexão
- Verifique sua conexão com a internet
- Confirme se o firewall não está bloqueando a porta 587

### Email não chega
- Verifique a pasta de spam
- Confirme se o email de destino está correto
- Teste com diferentes provedores de email

## Configurações Atuais do Sistema

O sistema está configurado para usar:
- **Host SMTP**: smtp.gmail.com
- **Porta**: 587
- **TLS**: Habilitado
- **Backend**: django.core.mail.backends.smtp.EmailBackend

## Funcionalidades que Usam Email

1. **Notificações de Vencimento**: Avisos de parcelas em atraso
2. **Alertas de Segurança**: Notificações de tentativas de acesso
3. **Backup**: Relatórios de status de backup
4. **NFe**: Envio de notas fiscais por email
5. **Relatórios Financeiros**: Envio de relatórios mensais

## Suporte

Se continuar com problemas:
1. Verifique os logs do Django no terminal
2. Teste com diferentes provedores de email
3. Consulte a documentação do seu provedor de email sobre SMTP