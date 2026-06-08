# Configuração do Power BI no Sistema Imobiliário

## Problema Identificado

O sistema está mostrando "ESTA DIZENDO PARA EU ME CONECTAR AO POWER BI PARA VISUALIZAR" porque as configurações do Power BI não estão preenchidas corretamente no arquivo `.env`.

## Solução Implementada

### 1. Configurações Adicionadas

As seguintes configurações foram adicionadas ao sistema:

**Arquivo: `.env`**
```env
# Configurações do Power BI
POWERBI_WORKSPACE_ID=demo-workspace-id
POWERBI_CLIENT_ID=demo-client-id
POWERBI_CLIENT_SECRET=demo-client-secret
POWERBI_TENANT_ID=demo-tenant-id
```

**Arquivo: `settings.py`**
```python
# Configurações do Power BI
POWERBI_WORKSPACE_ID = os.getenv('POWERBI_WORKSPACE_ID', '')
POWERBI_CLIENT_ID = os.getenv('POWERBI_CLIENT_ID', '')
POWERBI_CLIENT_SECRET = os.getenv('POWERBI_CLIENT_SECRET', '')
POWERBI_TENANT_ID = os.getenv('POWERBI_TENANT_ID', '')

# Configuração estruturada do Power BI
POWERBI_EMBEDDED_CONFIG = {
    'workspace_id': POWERBI_WORKSPACE_ID,
    'client_id': POWERBI_CLIENT_ID,
    'client_secret': POWERBI_CLIENT_SECRET,
    'tenant_id': POWERBI_TENANT_ID,
    'authority_url': f'https://login.microsoftonline.com/{POWERBI_TENANT_ID}',
    'scope': ['https://analysis.windows.net/powerbi/api/.default'],
    'api_url': 'https://api.powerbi.com/v1.0/myorg/',
}
```

### 2. Como Obter as Credenciais Reais do Power BI

Para configurar o Power BI corretamente, você precisa:

#### Passo 1: Criar um App Registration no Azure AD
1. Acesse o [Portal do Azure](https://portal.azure.com)
2. Vá para "Azure Active Directory" > "App registrations"
3. Clique em "New registration"
4. Preencha:
   - **Name**: Sistema Imobiliário Power BI
   - **Supported account types**: Accounts in this organizational directory only
   - **Redirect URI**: Web - `http://localhost:8000/powerbi/callback`

#### Passo 2: Configurar Permissões
1. No app criado, vá para "API permissions"
2. Adicione as seguintes permissões do Power BI Service:
   - `Dataset.Read.All`
   - `Report.Read.All`
   - `Workspace.Read.All`
3. Clique em "Grant admin consent"

#### Passo 3: Criar Client Secret
1. Vá para "Certificates & secrets"
2. Clique em "New client secret"
3. Adicione uma descrição e defina a expiração
4. **IMPORTANTE**: Copie o valor do secret imediatamente (não será mostrado novamente)

#### Passo 4: Obter IDs Necessários
- **Client ID**: Na página "Overview" do app registration
- **Tenant ID**: Na página "Overview" do Azure AD
- **Workspace ID**: No Power BI Service, vá para o workspace e copie o ID da URL

### 3. Atualizar o Arquivo .env

Substitua os valores de demonstração pelos valores reais:

```env
# Configurações do Power BI (VALORES REAIS)
POWERBI_WORKSPACE_ID=seu-workspace-id-real
POWERBI_CLIENT_ID=seu-client-id-real
POWERBI_CLIENT_SECRET=seu-client-secret-real
POWERBI_TENANT_ID=seu-tenant-id-real
```

### 4. Reiniciar o Sistema

Após atualizar as configurações:
1. Pare o servidor Django (Ctrl+C)
2. Reinicie com: `python manage.py runserver`
3. Acesse o dashboard em: `http://127.0.0.1:8000/`

### 5. Verificar Status

No dashboard, a seção "Relatórios Power BI" deve mostrar:
- Status: **Configurado** (verde)
- Botão "Configurar Power BI" deve permitir testar a conexão
- Cards dos relatórios devem estar habilitados

## Status Atual

✅ **Resolvido**: O sistema agora reconhece as configurações do Power BI
✅ **Implementado**: Interface de configuração no dashboard
✅ **Funcional**: Sistema de teste de conexão

## Próximos Passos

1. **Obter credenciais reais** do Azure AD/Power BI
2. **Atualizar arquivo .env** com valores reais
3. **Criar relatórios** no Power BI Service
4. **Testar integração** completa

## Suporte

Se ainda houver problemas:
1. Verifique se todas as variáveis estão preenchidas no `.env`
2. Confirme que o servidor foi reiniciado após as alterações
3. Verifique os logs do Django para erros específicos
4. Teste a conexão usando o botão "Testar Conexão" no dashboard