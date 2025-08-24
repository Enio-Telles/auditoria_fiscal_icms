# API Mock para Sistema de Agentes

Este diretório contém uma API mock simples para desenvolvimento e teste da interface de agentes.

## Estrutura

- `mock_agents_api.py` - Servidor mock que simula os endpoints de agentes
- `mock_data.py` - Dados simulados para agentes, tarefas e workflows

## Como usar

1. Execute o servidor mock:
```bash
python mock_agents_api.py
```

2. A API ficará disponível em `http://localhost:8007`

3. Configure o frontend para usar esta URL durante o desenvolvimento

## Endpoints Disponíveis

- GET `/agents/status` - Status do sistema
- GET `/agents/metrics` - Métricas do sistema
- GET `/agents` - Lista de agentes
- POST `/agents` - Criar agente
- GET `/agents/{id}` - Detalhes do agente
- POST `/agents/{id}/start` - Iniciar agente
- POST `/agents/{id}/stop` - Parar agente
- DELETE `/agents/{id}` - Remover agente
- GET `/agents/tasks` - Lista de tarefas
- POST `/agents/quick-classify` - Classificação rápida
- GET `/agents/workflows` - Lista de workflows
