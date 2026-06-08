# Power BI Integration

Este módulo fornece APIs REST para integração com o Microsoft Power BI, permitindo a criação de dashboards e relatórios avançados com dados do sistema imobiliário.

## Funcionalidades

### APIs Disponíveis

1. **Dashboard Geral** (`/powerbi/dashboard/`)
   - Dados consolidados para visão geral do negócio
   - Métricas de imóveis, contratos, receitas e despesas

2. **Imóveis** (`/powerbi/imoveis/`)
   - Lista completa de imóveis com detalhes
   - Informações de localização, características e status

3. **Financeiro** (`/powerbi/financeiro/`)
   - Dados de parcelas, pagamentos e inadimplência
   - Análise de receitas e despesas por período

4. **Contratos** (`/powerbi/contratos/`)
   - Informações detalhadas dos contratos
   - Status, valores e datas importantes

5. **Manutenção** (`/powerbi/manutencao/`)
   - Ordens de serviço e custos de manutenção
   - Análise de gastos por imóvel e tipo de serviço

6. **Inquilinos** (`/powerbi/inquilinos/`)
   - Dados dos inquilinos e histórico
   - Informações de contato e contratos

7. **Proprietários** (`/powerbi/proprietarios/`)
   - Informações dos proprietários
   - Portfolio de imóveis e receitas

### Utilitários

- **Datasets** (`/powerbi/datasets/`): Lista todos os datasets disponíveis
- **Health Check** (`/powerbi/health/`): Verifica o status da API

## Configuração

### 1. Configuração no Django Admin

Acesse o Django Admin e configure:

1. **Power BI Config**: Configurações de conexão com o Power BI
2. **Power BI Dataset**: Defina os datasets disponíveis
3. **Power BI Token**: Gerencie tokens de acesso

### 2. Autenticação

As APIs utilizam autenticação baseada em token. Para acessar:

```python
headers = {
    'Authorization': 'Token seu_token_aqui',
    'Content-Type': 'application/json'
}
```

### 3. Exemplo de Uso

```python
import requests

# Configurar headers
headers = {
    'Authorization': 'Token seu_token_aqui',
    'Content-Type': 'application/json'
}

# Buscar dados do dashboard
response = requests.get(
    'http://localhost:8000/powerbi/dashboard/',
    headers=headers
)

data = response.json()
print(data)
```

## Conectando ao Power BI

### 1. No Power BI Desktop

1. Abra o Power BI Desktop
2. Clique em "Obter Dados" > "Web"
3. Insira a URL da API: `http://localhost:8000/powerbi/dashboard/`
4. Configure a autenticação:
   - Método: "Cabeçalho HTTP"
   - Nome do cabeçalho: "Authorization"
   - Valor: "Token seu_token_aqui"

### 2. Configuração de Atualização

Para atualização automática dos dados:

1. Configure a fonte de dados com as credenciais
2. Defina o agendamento de atualização
3. Publique no Power BI Service

## Segurança

- Todas as APIs requerem autenticação
- Logs de acesso são registrados automaticamente
- Dados sensíveis são criptografados
- Rate limiting aplicado para prevenir abuso

## Monitoramento

- **Logs de Acesso**: Registrados na tabela `PowerBIAccessLog`
- **Health Check**: Endpoint `/powerbi/health/` para monitoramento
- **Métricas**: Disponíveis através do Django Admin

## Troubleshooting

### Erro de Autenticação
- Verifique se o token está correto
- Confirme se o usuário tem permissões adequadas

### Dados Não Atualizados
- Verifique a conectividade com o banco de dados
- Confirme se as migrações foram aplicadas

### Performance
- Use filtros de data para reduzir o volume de dados
- Configure cache se necessário
- Monitore os logs de acesso para identificar gargalos

## Suporte

Para suporte técnico, consulte:
- Logs do Django
- Django Admin (seção Power BI)
- Documentação da API REST Framework