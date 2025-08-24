# Sistema de Agentes para Auditoria Fiscal ICMS

## 🤖 Visão Geral

Este sistema implementa uma arquitetura de agentes especializados para automatizar processos de auditoria fiscal ICMS. Cada agente é responsável por uma área específica de conhecimento, trabalhando de forma independente ou coordenada através de workflows.

## 🏗️ Arquitetura

```
src/agents/
├── base_agent.py          # Classe base para todos os agentes
├── expansion_agent.py     # Expansão e enriquecimento de dados
├── aggregation_agent.py   # Agregação e análise estatística
├── ncm_agent.py          # Classificação NCM especializada
├── cest_agent.py         # Classificação CEST e análise ST
├── reconciler_agent.py   # Reconciliação e qualidade de dados
├── agent_manager.py      # Gerenciamento de ciclo de vida
├── agent_coordinator.py  # Orquestração de workflows
└── __init__.py           # Interface pública e utilitários
```

## 🎯 Agentes Especializados

### 1. **ExpansionAgent** - Expansão de Dados
- **Objetivo**: Enriquecer descrições de produtos com informações técnicas
- **Capacidades**:
  - `expand_description`: Expande descrições curtas em descrições detalhadas
  - `normalize_text`: Normaliza e padroniza textos
  - `extract_features`: Extrai características técnicas
  - `identify_technical_specs`: Identifica especificações técnicas
  - `suggest_synonyms`: Sugere sinônimos e termos relacionados

### 2. **NCMAgent** - Classificação NCM
- **Objetivo**: Classificar produtos no sistema NCM (Nomenclatura Comum do Mercosul)
- **Capacidades**:
  - `classify_ncm`: Classifica produto com código NCM
  - `validate_ncm`: Valida códigos NCM existentes
  - `suggest_alternatives`: Sugere códigos NCM alternativos
  - `detect_inconsistencies`: Detecta inconsistências em classificações
  - `explain_classification`: Explica processo de classificação

### 3. **CESTAgent** - Classificação CEST
- **Objetivo**: Classificar produtos no sistema CEST e analisar Substituição Tributária
- **Capacidades**:
  - `classify_cest`: Classifica produto com código CEST
  - `validate_cest`: Valida códigos CEST existentes
  - `map_ncm_to_cest`: Mapeia NCM para possíveis CEST
  - `analyze_st_requirement`: Analisa exigência de ST
  - `suggest_alternatives`: Sugere códigos CEST alternativos

### 4. **AggregationAgent** - Agregação e Análise
- **Objetivo**: Consolidar dados de múltiplas fontes e gerar análises estatísticas
- **Capacidades**:
  - `consolidate_data`: Consolida dados de diferentes fontes
  - `aggregate_statistics`: Calcula estatísticas agregadas
  - `detect_patterns`: Detecta padrões nos dados
  - `generate_report`: Gera relatórios consolidados
  - `analyze_trends`: Analisa tendências temporais

### 5. **ReconcilerAgent** - Reconciliação de Dados
- **Objetivo**: Garantir qualidade e consistência dos dados
- **Capacidades**:
  - `reconcile_datasets`: Reconcilia múltiplos datasets
  - `detect_inconsistencies`: Detecta inconsistências
  - `validate_data_integrity`: Valida integridade dos dados
  - `analyze_data_quality`: Analisa qualidade geral
  - `merge_duplicate_records`: Mescla registros duplicados

## 🔧 Componentes de Gerenciamento

### AgentManager
- **Responsabilidade**: Gerenciar ciclo de vida dos agentes
- **Funcionalidades**:
  - Registro e criação de agentes
  - Monitoramento de saúde e performance
  - Distribuição de tarefas
  - Coleta de métricas
  - Recuperação de falhas

### AgentCoordinator
- **Responsabilidade**: Orquestrar workflows multi-agente
- **Funcionalidades**:
  - Definição de workflows complexos
  - Execução paralela e sequencial
  - Gerenciamento de dependências
  - Monitoramento de progresso
  - Templates de workflow

## 🚀 Uso Básico

### Configuração Inicial

```python
from src.agents import create_audit_agent_system

# Criar sistema completo
agent_manager, agent_coordinator = create_audit_agent_system()

# Iniciar sistema
await agent_manager.start()
await agent_coordinator.start()
```

### Uso de Agente Individual

```python
from src.agents import AgentTask, TaskPriority

# Criar agente
await agent_manager.create_agent("NCMAgent", "ncm_classifier")
await agent_manager.start_agent("ncm_classifier")

# Executar tarefa
task = AgentTask(
    type="classify_ncm",
    data={"description": "Pneu radial 185/65 R15"},
    priority=TaskPriority.HIGH
)

result = await agent_manager.execute_task("ncm_classifier", task)
print(f"NCM: {result['ncm_code']} - Confiança: {result['confidence']:.2%}")
```

### Uso de Workflow

```python
# Criar workflow personalizado
workflow_id = agent_coordinator.create_workflow(
    workflow_id="product_audit_001",
    name="Auditoria Completa de Produto",
    description="Classificação NCM/CEST + validação",
    steps=[
        {
            "id": "expand_data",
            "agent_name": "expansion_agent",
            "task_type": "expand_description",
            "task_data": {"description": "${product_description}"},
            "dependencies": []
        },
        {
            "id": "classify_ncm",
            "agent_name": "ncm_agent",
            "task_type": "classify_ncm", 
            "task_data": {"description": "${step_expand_data_result.expanded_description}"},
            "dependencies": ["expand_data"]
        }
    ]
)

# Executar workflow
await agent_coordinator.execute_workflow(workflow_id, {
    "product_description": "Medicamento Paracetamol 500mg"
})
```

### Função Utilitária Rápida

```python
from src.agents import quick_classify_product

# Classificação rápida e simples
result = await quick_classify_product(
    "Notebook Dell Core i5 8GB RAM",
    state="SP"
)

if result["success"]:
    summary = result["summary"]
    print(f"NCM: {summary['ncm_code']}")
    print(f"CEST: {summary['cest_code']}")
```

## 📊 Workflows Pré-definidos

### 1. Classificação Completa de Produto
**Template**: `product_classification`

Fluxo completo que:
1. Expande descrição do produto
2. Classifica NCM baseado na descrição expandida
3. Classifica CEST baseado em NCM e estado
4. Consolida todos os resultados

### 2. Reconciliação de Dados
**Template**: `data_reconciliation`

Processo de qualidade que:
1. Detecta inconsistências no dataset
2. Analisa qualidade geral dos dados
3. Sugere correções automáticas
4. Gera relatório consolidado de qualidade

## 🔍 Monitoramento e Métricas

### Métricas dos Agentes
```python
# Status de um agente específico
agent_info = agent_manager.get_agent_info("ncm_classifier")
print(f"Status: {agent_info['status']}")
print(f"Tarefas concluídas: {agent_info['metrics']['tasks_completed']}")

# Métricas do sistema
system_metrics = agent_manager.get_system_metrics()
print(f"Taxa de sucesso: {system_metrics['task_metrics']['success_rate_percentage']:.1f}%")
```

### Métricas de Workflows
```python
# Status de workflow
workflow_status = agent_coordinator.get_workflow_status("workflow_001")
print(f"Progresso: {workflow_status['progress_percentage']:.1f}%")

# Métricas gerais de workflows
workflow_metrics = agent_coordinator.get_workflow_metrics()
print(f"Workflows ativos: {workflow_metrics['overview']['running_workflows']}")
```

## 🛠️ Configuração Avançada

### Configurações Personalizadas

```python
config = {
    "manager": {
        "health_check_interval": 60,
        "max_retry_attempts": 5,
        "task_timeout": 600
    },
    "coordinator": {
        "max_concurrent_workflows": 20,
        "default_step_timeout": 300
    }
}

agent_manager, agent_coordinator = create_audit_agent_system(config)
```

### Configuração de Agente Específico

```python
ncm_config = {
    "confidence_threshold": 0.8,
    "max_suggestions": 10,
    "enable_semantic_analysis": True,
    "cache_size": 5000
}

await agent_manager.create_agent("NCMAgent", "ncm_agent", ncm_config)
```

## 📈 Casos de Uso

### 1. **Auditoria Fiscal Automatizada**
- Classificação automática de produtos importados
- Validação de códigos NCM/CEST em notas fiscais
- Detecção de inconsistências tributárias

### 2. **Qualidade de Dados**
- Limpeza de bases de produtos
- Reconciliação entre sistemas diferentes
- Padronização de descrições

### 3. **Análise de Tendências**
- Análise de padrões de classificação
- Identificação de produtos problemáticos
- Relatórios de performance tributária

### 4. **Processamento em Lote**
- Classificação de grandes volumes de produtos
- Validação de bases históricas
- Migração entre sistemas

## 🔧 Extensibilidade

### Criando um Novo Agente

```python
from src.agents import BaseAgent, AgentTask

class CustomAgent(BaseAgent):
    def __init__(self, config=None):
        super().__init__(name="CustomAgent", config=config)
    
    def get_capabilities(self):
        return ["custom_task"]
    
    async def process_task(self, task: AgentTask):
        if task.type == "custom_task":
            return await self._custom_processing(task.data)
        raise ValueError(f"Tarefa não suportada: {task.type}")
    
    async def _custom_processing(self, data):
        # Implementar lógica personalizada
        return {"result": "processed"}

# Registrar no sistema
agent_manager.register_agent_type(CustomAgent, "CustomAgent")
```

### Criando Template de Workflow

```python
custom_template = {
    "name": "Processo Personalizado",
    "description": "Workflow customizado para necessidade específica",
    "steps": [
        # Definir steps personalizados
    ]
}

agent_coordinator.register_workflow_template("custom_process", custom_template)
```

## 🧪 Testes e Exemplos

Execute o arquivo de exemplo para ver o sistema em ação:

```bash
python exemplo_uso_agentes.py
```

O exemplo demonstra:
- Uso de agentes individuais
- Execução de workflows completos
- Reconciliação de dados
- Função de classificação rápida

## 📝 Logs e Debugging

Todos os agentes geram logs detalhados:

```python
import logging

# Configurar nível de log
logging.basicConfig(level=logging.INFO)

# Logs específicos por agente
logger = logging.getLogger("src.agents.ncm_agent")
logger.setLevel(logging.DEBUG)
```

## 🔐 Considerações de Segurança

- Validação de entrada em todas as tarefas
- Timeout automático para prevenir travamentos
- Isolamento de falhas entre agentes
- Logs de auditoria para rastreabilidade

## 📋 Limitações Conhecidas

1. **Base de Conhecimento**: Bases NCM/CEST simplificadas para demonstração
2. **Escalabilidade**: Otimizado para volumes médios (< 100k registros)
3. **Persistência**: Cache em memória (não persistente entre sessões)
4. **Conectividade**: Não inclui integração com APIs externas

## 🚦 Status do Projeto

- ✅ **Implementado**: Todos os agentes especializados
- ✅ **Implementado**: Sistema de gerenciamento completo
- ✅ **Implementado**: Workflows e orquestração
- ✅ **Implementado**: Exemplos e documentação
- 🔄 **Em desenvolvimento**: Integração com APIs externas
- 📋 **Planejado**: Interface web para monitoramento
- 📋 **Planejado**: Persistência de dados

## 🤝 Contribuição

Para contribuir com o projeto:

1. Crie novos agentes especializados
2. Implemente melhorias nos agentes existentes
3. Adicione novos templates de workflow
4. Melhore a documentação e exemplos

## 📞 Suporte

Para dúvidas e suporte:
- Consulte os exemplos em `exemplo_uso_agentes.py`
- Verifique a documentação inline no código
- Analise os logs para debugging
