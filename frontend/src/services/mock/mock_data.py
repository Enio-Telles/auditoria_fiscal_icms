# Dados simulados para a API mock de agentes
from datetime import datetime, timedelta
import random
import uuid

def generate_id():
    return str(uuid.uuid4())[:8]

# Status possíveis
STATUSES = ['idle', 'running', 'busy', 'error', 'stopped']
TASK_STATUSES = ['pending', 'running', 'completed', 'failed']
WORKFLOW_STATUSES = ['idle', 'running', 'completed', 'failed', 'paused']

# Tipos de agentes
AGENT_TYPES = {
    'ExpansionAgent': 'Expansão e enriquecimento de dados de produtos',
    'NCMAgent': 'Classificação NCM especializada com validação hierárquica',
    'CESTAgent': 'Classificação CEST e análise de Substituição Tributária',
    'AggregationAgent': 'Agregação estatística e análise de tendências',
    'ReconcilerAgent': 'Reconciliação e qualidade de dados multi-fonte',
}

# Capacidades por tipo de agente
AGENT_CAPABILITIES = {
    'ExpansionAgent': ['expand_description', 'normalize_text', 'extract_features', 'identify_technical_specs', 'suggest_synonyms'],
    'NCMAgent': ['classify_ncm', 'validate_ncm', 'suggest_alternatives', 'detect_inconsistencies', 'explain_classification'],
    'CESTAgent': ['classify_cest', 'validate_cest', 'map_ncm_to_cest', 'analyze_st_requirement', 'suggest_alternatives'],
    'AggregationAgent': ['consolidate_data', 'aggregate_statistics', 'detect_patterns', 'generate_report', 'analyze_trends'],
    'ReconcilerAgent': ['reconcile_datasets', 'detect_inconsistencies', 'validate_data_integrity', 'analyze_data_quality', 'merge_duplicate_records'],
}

def generate_agent_metrics():
    tasks_completed = random.randint(50, 500)
    tasks_failed = random.randint(0, 20)
    total_tasks = tasks_completed + tasks_failed
    success_rate = (tasks_completed / total_tasks * 100) if total_tasks > 0 else 100
    
    return {
        'tasks_completed': tasks_completed,
        'tasks_failed': tasks_failed,
        'average_processing_time': round(random.uniform(0.5, 5.0), 2),
        'cache_hits': random.randint(100, 1000),
        'cache_misses': random.randint(10, 100),
        'success_rate_percentage': round(success_rate, 1),
        'last_task_time': (datetime.now() - timedelta(minutes=random.randint(1, 60))).isoformat(),
        'uptime_seconds': random.randint(3600, 86400),  # 1 hora a 1 dia
    }

def generate_agent():
    agent_type = random.choice(list(AGENT_TYPES.keys()))
    agent_id = generate_id()
    
    return {
        'id': agent_id,
        'name': f"{agent_type.lower()}_{agent_id}",
        'type': agent_type,
        'status': random.choice(['idle', 'running', 'busy']),
        'created_at': (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat(),
        'last_heartbeat': (datetime.now() - timedelta(minutes=random.randint(0, 5))).isoformat(),
        'config': {
            'confidence_threshold': round(random.uniform(0.7, 0.9), 2),
            'cache_size': random.choice([1000, 5000, 10000]),
            'timeout_seconds': random.choice([30, 60, 120]),
            'max_retries': random.randint(3, 10),
            'enable_cache': True,
        },
        'metrics': generate_agent_metrics(),
        'capabilities': AGENT_CAPABILITIES.get(agent_type, []),
    }

def generate_task(agent_id=None):
    if not agent_id:
        agent_id = generate_id()
    
    task_types = ['classify_ncm', 'classify_cest', 'expand_description', 'consolidate_data', 'reconcile_datasets']
    task_type = random.choice(task_types)
    
    created_at = datetime.now() - timedelta(minutes=random.randint(1, 120))
    started_at = created_at + timedelta(seconds=random.randint(1, 10)) if random.choice([True, False]) else None
    
    status = random.choice(TASK_STATUSES)
    completed_at = None
    processing_time = None
    
    if status == 'completed' and started_at:
        processing_time = round(random.uniform(0.5, 10.0), 2)
        completed_at = started_at + timedelta(seconds=processing_time)
    elif status == 'failed' and started_at:
        processing_time = round(random.uniform(0.1, 5.0), 2)
        completed_at = started_at + timedelta(seconds=processing_time)
    
    return {
        'id': generate_id(),
        'type': task_type,
        'status': status,
        'agent_id': agent_id,
        'created_at': created_at.isoformat(),
        'started_at': started_at.isoformat() if started_at else None,
        'completed_at': completed_at.isoformat() if completed_at else None,
        'priority': random.choice(['low', 'medium', 'high', 'urgent']),
        'data': {
            'description': f"Tarefa de {task_type} para produto exemplo",
            'params': {'confidence_threshold': 0.8}
        },
        'result': {
            'classification': 'Resultado simulado',
            'confidence': round(random.uniform(0.7, 0.95), 2)
        } if status == 'completed' else None,
        'error': 'Erro simulado durante processamento' if status == 'failed' else None,
        'processing_time': processing_time,
    }

def generate_workflow():
    workflow_id = generate_id()
    total_steps = random.randint(3, 8)
    completed_steps = random.randint(0, total_steps)
    failed_steps = random.randint(0, max(0, total_steps - completed_steps))
    
    progress = (completed_steps / total_steps * 100) if total_steps > 0 else 0
    
    created_at = datetime.now() - timedelta(hours=random.randint(1, 24))
    started_at = created_at + timedelta(minutes=random.randint(1, 10)) if random.choice([True, False]) else None
    
    status = random.choice(WORKFLOW_STATUSES)
    completed_at = None
    
    if status == 'completed' and started_at:
        completed_at = started_at + timedelta(minutes=random.randint(5, 60))
    
    return {
        'id': workflow_id,
        'name': f"Workflow de Classificação {workflow_id}",
        'description': "Workflow automatizado para classificação completa de produtos",
        'status': status,
        'created_at': created_at.isoformat(),
        'started_at': started_at.isoformat() if started_at else None,
        'completed_at': completed_at.isoformat() if completed_at else None,
        'progress_percentage': round(progress, 1),
        'total_steps': total_steps,
        'completed_steps': completed_steps,
        'failed_steps': failed_steps,
        'current_step': f"step_{random.randint(1, total_steps)}" if status == 'running' else None,
        'steps': [
            {
                'id': f"step_{i}",
                'name': f"Etapa {i+1}",
                'status': 'completed' if i < completed_steps else 'failed' if i < completed_steps + failed_steps else 'pending',
                'agent_name': random.choice(list(AGENT_TYPES.keys())),
                'task_type': random.choice(['classify_ncm', 'classify_cest', 'expand_description']),
                'dependencies': [f"step_{j}" for j in range(max(0, i-1), i)],
                'started_at': (started_at + timedelta(minutes=i*5)).isoformat() if started_at and i < completed_steps else None,
                'completed_at': (started_at + timedelta(minutes=i*5+3)).isoformat() if started_at and i < completed_steps else None,
                'result': {'status': 'success'} if i < completed_steps else None,
                'error': 'Erro na etapa' if i >= completed_steps and i < completed_steps + failed_steps else None,
            }
            for i in range(total_steps)
        ],
        'context': {
            'product_description': 'Produto de exemplo para classificação',
            'state': 'SP'
        },
        'error_message': 'Erro no workflow' if status == 'failed' else None,
    }

def generate_system_metrics():
    total_agents = random.randint(3, 8)
    running_agents = random.randint(1, total_agents)
    idle_agents = total_agents - running_agents
    error_agents = random.randint(0, 1)
    
    total_workflows = random.randint(10, 50)
    running_workflows = random.randint(1, 5)
    completed_workflows = random.randint(5, total_workflows - running_workflows)
    failed_workflows = total_workflows - running_workflows - completed_workflows
    
    return {
        'agent_metrics': {
            'total_agents': total_agents,
            'running_agents': running_agents,
            'idle_agents': idle_agents,
            'error_agents': error_agents,
            'total_tasks_processed': random.randint(1000, 10000),
            'average_success_rate': round(random.uniform(85, 98), 1),
        },
        'workflow_metrics': {
            'total_workflows': total_workflows,
            'running_workflows': running_workflows,
            'completed_workflows': completed_workflows,
            'failed_workflows': failed_workflows,
            'average_completion_time': round(random.uniform(30, 300), 2),
        },
        'performance_metrics': {
            'cpu_usage_percentage': round(random.uniform(10, 80), 1),
            'memory_usage_percentage': round(random.uniform(20, 70), 1),
            'cache_hit_rate_percentage': round(random.uniform(75, 95), 1),
            'average_response_time': round(random.uniform(0.1, 2.0), 2),
        },
        'timestamp': datetime.now().isoformat(),
    }

# Gerar dados iniciais
def get_mock_data():
    agents = [generate_agent() for _ in range(5)]
    tasks = []
    
    # Gerar algumas tarefas para cada agente
    for agent in agents:
        num_tasks = random.randint(2, 8)
        for _ in range(num_tasks):
            tasks.append(generate_task(agent['id']))
    
    # Gerar algumas tarefas sem agente específico
    for _ in range(10):
        tasks.append(generate_task())
    
    workflows = [generate_workflow() for _ in range(3)]
    
    return {
        'agents': agents,
        'tasks': tasks,
        'workflows': workflows,
        'system_metrics': generate_system_metrics(),
    }
