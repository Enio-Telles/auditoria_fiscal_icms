// Tipos TypeScript para o Sistema de Agentes

export interface AgentStatus {
  IDLE: 'idle';
  RUNNING: 'running';
  BUSY: 'busy';
  ERROR: 'error';
  STOPPED: 'stopped';
}

export interface TaskPriority {
  LOW: 'low';
  MEDIUM: 'medium';
  HIGH: 'high';
  URGENT: 'urgent';
}

export interface TaskStatus {
  PENDING: 'pending';
  RUNNING: 'running';
  COMPLETED: 'completed';
  FAILED: 'failed';
}

export interface WorkflowStatus {
  IDLE: 'idle';
  RUNNING: 'running';
  COMPLETED: 'completed';
  FAILED: 'failed';
  PAUSED: 'paused';
}

export interface AgentType {
  EXPANSION: 'ExpansionAgent';
  NCM: 'NCMAgent';
  CEST: 'CESTAgent';
  AGGREGATION: 'AggregationAgent';
  RECONCILER: 'ReconcilerAgent';
}

export interface AgentCapabilities {
  [key: string]: string[];
}

export interface AgentMetrics {
  tasks_completed: number;
  tasks_failed: number;
  average_processing_time: number;
  cache_hits: number;
  cache_misses: number;
  success_rate_percentage: number;
  last_task_time?: string;
  uptime_seconds: number;
}

export interface AgentConfig {
  confidence_threshold?: number;
  cache_size?: number;
  timeout_seconds?: number;
  max_retries?: number;
  enable_cache?: boolean;
  [key: string]: any;
}

export interface Agent {
  id: string;
  name: string;
  type: keyof AgentType;
  status: keyof AgentStatus;
  created_at: string;
  last_heartbeat?: string;
  config: AgentConfig;
  metrics: AgentMetrics;
  capabilities: string[];
  error_message?: string;
}

export interface Task {
  id: string;
  type: string;
  status: keyof TaskStatus;
  agent_id: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  priority: keyof TaskPriority;
  data: Record<string, any>;
  result?: Record<string, any>;
  error?: string;
  processing_time?: number;
}

export interface WorkflowStep {
  id: string;
  name: string;
  status: keyof TaskStatus;
  agent_name: string;
  task_type: string;
  dependencies: string[];
  started_at?: string;
  completed_at?: string;
  result?: Record<string, any>;
  error?: string;
  timeout_seconds?: number;
}

export interface Workflow {
  id: string;
  name: string;
  description: string;
  status: keyof WorkflowStatus;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  progress_percentage: number;
  total_steps: number;
  completed_steps: number;
  failed_steps: number;
  current_step?: string;
  steps: WorkflowStep[];
  context?: Record<string, any>;
  error_message?: string;
}

export interface SystemMetrics {
  agent_metrics: {
    total_agents: number;
    running_agents: number;
    idle_agents: number;
    error_agents: number;
    total_tasks_processed: number;
    average_success_rate: number;
  };
  workflow_metrics: {
    total_workflows: number;
    running_workflows: number;
    completed_workflows: number;
    failed_workflows: number;
    average_completion_time: number;
  };
  performance_metrics: {
    cpu_usage_percentage: number;
    memory_usage_percentage: number;
    cache_hit_rate_percentage: number;
    average_response_time: number;
  };
  timestamp: string;
}

export interface ClassificationRequest {
  description: string;
  state?: string;
  confidence_threshold?: number;
  include_details?: boolean;
}

export interface ClassificationResult {
  success: boolean;
  summary: {
    ncm_code: string;
    ncm_description: string;
    cest_code?: string;
    cest_description?: string;
    confidence: number;
    st_required?: boolean;
  };
  details: {
    expansion_result?: Record<string, any>;
    ncm_result?: Record<string, any>;
    cest_result?: Record<string, any>;
    processing_time: number;
    agent_info?: Record<string, any>;
  };
  errors?: string[];
  workflow_id?: string;
}

export interface AgentLog {
  timestamp: string;
  level: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR';
  agent_id?: string;
  message: string;
  details?: Record<string, any>;
}

export interface SystemStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  message: string;
  agents: Record<string, string>;
  uptime_seconds: number;
  version: string;
}

// Constantes para os tipos de agentes disponíveis
export const AGENT_TYPES = {
  EXPANSION: 'ExpansionAgent',
  NCM: 'NCMAgent',
  CEST: 'CESTAgent',
  AGGREGATION: 'AggregationAgent',
  RECONCILER: 'ReconcilerAgent',
} as const;

// Constantes para status
export const AGENT_STATUSES = {
  IDLE: 'idle',
  RUNNING: 'running',
  BUSY: 'busy',
  ERROR: 'error',
  STOPPED: 'stopped',
} as const;

export const TASK_STATUSES = {
  PENDING: 'pending',
  RUNNING: 'running',
  COMPLETED: 'completed',
  FAILED: 'failed',
} as const;

export const WORKFLOW_STATUSES = {
  IDLE: 'idle',
  RUNNING: 'running',
  COMPLETED: 'completed',
  FAILED: 'failed',
  PAUSED: 'paused',
} as const;

export const TASK_PRIORITIES = {
  LOW: 'low',
  MEDIUM: 'medium',
  HIGH: 'high',
  URGENT: 'urgent',
} as const;

// Mapeamento de cores para status
export const STATUS_COLORS = {
  // Agent Status
  'idle': '#9e9e9e',
  'running': '#4caf50',
  'busy': '#ff9800',
  'error': '#f44336',
  'stopped': '#757575',
  // Task Status
  'pending': '#9e9e9e',
  'task_running': '#2196f3',
  'completed': '#4caf50',
  'failed': '#f44336',
  // Workflow Status
  'workflow_idle': '#9e9e9e',
  'workflow_running': '#2196f3',
  'workflow_completed': '#4caf50',
  'workflow_failed': '#f44336',
  'paused': '#ff9800',
} as const;

// Descrições dos tipos de agentes
export const AGENT_DESCRIPTIONS = {
  [AGENT_TYPES.EXPANSION]: 'Expansão e enriquecimento de dados de produtos',
  [AGENT_TYPES.NCM]: 'Classificação NCM especializada com validação hierárquica',
  [AGENT_TYPES.CEST]: 'Classificação CEST e análise de Substituição Tributária',
  [AGENT_TYPES.AGGREGATION]: 'Agregação estatística e análise de tendências',
  [AGENT_TYPES.RECONCILER]: 'Reconciliação e qualidade de dados multi-fonte',
} as const;
