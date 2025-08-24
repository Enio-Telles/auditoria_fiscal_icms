// Serviço para comunicação com a API de Agentes
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8003';

export interface AgentInfo {
  id: string;
  name: string;
  type: string;
  status: 'idle' | 'running' | 'busy' | 'error' | 'stopped';
  created_at: string;
  last_heartbeat?: string;
  config: Record<string, any>;
  metrics: {
    tasks_completed: number;
    tasks_failed: number;
    average_processing_time: number;
    cache_hits: number;
    cache_misses: number;
    success_rate_percentage: number;
  };
}

export interface AgentTask {
  id: string;
  type: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  agent_id: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  data: Record<string, any>;
  result?: Record<string, any>;
  error?: string;
}

export interface WorkflowInfo {
  id: string;
  name: string;
  description: string;
  status: 'idle' | 'running' | 'completed' | 'failed' | 'paused';
  created_at: string;
  started_at?: string;
  completed_at?: string;
  progress_percentage: number;
  total_steps: number;
  completed_steps: number;
  failed_steps: number;
  current_step?: string;
  steps: WorkflowStep[];
}

export interface WorkflowStep {
  id: string;
  name: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
  agent_name: string;
  task_type: string;
  dependencies: string[];
  started_at?: string;
  completed_at?: string;
  result?: Record<string, any>;
  error?: string;
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
}

export interface QuickClassifyRequest {
  description: string;
  state?: string;
}

export interface QuickClassifyResult {
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
  };
  errors?: string[];
}

class AgentsService {
  private api = axios.create({
    baseURL: API_BASE_URL,
    timeout: 30000,
  });

  // Sistema de Agentes
  async getSystemStatus(): Promise<{ status: string; message: string }> {
    const response = await this.api.get('/agents/status');
    return response.data;
  }

  async getSystemMetrics(): Promise<SystemMetrics> {
    const response = await this.api.get('/agents/metrics');
    return response.data;
  }

  async initializeSystem(): Promise<{ success: boolean; message: string }> {
    const response = await this.api.post('/agents/initialize');
    return response.data;
  }

  async shutdownSystem(): Promise<{ success: boolean; message: string }> {
    const response = await this.api.post('/agents/shutdown');
    return response.data;
  }

  // Gerenciamento de Agentes
  async getAgents(): Promise<AgentInfo[]> {
    const response = await this.api.get('/agents');
    return response.data;
  }

  async getAgent(agentId: string): Promise<AgentInfo> {
    const response = await this.api.get(`/agents/${agentId}`);
    return response.data;
  }

  async createAgent(agentType: string, config?: Record<string, any>): Promise<AgentInfo> {
    const response = await this.api.post('/agents', {
      agent_type: agentType,
      config: config || {}
    });
    return response.data;
  }

  async startAgent(agentId: string): Promise<{ success: boolean; message: string }> {
    const response = await this.api.post(`/agents/${agentId}/start`);
    return response.data;
  }

  async stopAgent(agentId: string): Promise<{ success: boolean; message: string }> {
    const response = await this.api.post(`/agents/${agentId}/stop`);
    return response.data;
  }

  async removeAgent(agentId: string): Promise<{ success: boolean; message: string }> {
    const response = await this.api.delete(`/agents/${agentId}`);
    return response.data;
  }

  async restartAgent(agentId: string): Promise<{ success: boolean; message: string }> {
    const response = await this.api.post(`/agents/${agentId}/restart`);
    return response.data;
  }

  async updateAgentConfig(agentId: string, config: Record<string, any>): Promise<AgentInfo> {
    const response = await this.api.put(`/agents/${agentId}/config`, config);
    return response.data;
  }

  // Tarefas
  async getAgentTasks(agentId: string): Promise<AgentTask[]> {
    const response = await this.api.get(`/agents/${agentId}/tasks`);
    return response.data;
  }

  async getAllTasks(): Promise<AgentTask[]> {
    const response = await this.api.get('/agents/tasks');
    return response.data;
  }

  async executeTask(agentId: string, taskType: string, taskData: Record<string, any>): Promise<AgentTask> {
    const response = await this.api.post(`/agents/${agentId}/execute`, {
      task_type: taskType,
      data: taskData
    });
    return response.data;
  }

  async getTaskResult(taskId: string): Promise<AgentTask> {
    const response = await this.api.get(`/agents/tasks/${taskId}`);
    return response.data;
  }

  // Workflows
  async getWorkflows(): Promise<WorkflowInfo[]> {
    const response = await this.api.get('/agents/workflows');
    return response.data;
  }

  async getWorkflow(workflowId: string): Promise<WorkflowInfo> {
    const response = await this.api.get(`/agents/workflows/${workflowId}`);
    return response.data;
  }

  async createWorkflow(name: string, steps: any[]): Promise<WorkflowInfo> {
    const response = await this.api.post('/agents/workflows', {
      name,
      steps
    });
    return response.data;
  }

  async executeWorkflow(workflowId: string, context: Record<string, any>): Promise<{ workflow_id: string; execution_id: string }> {
    const response = await this.api.post(`/agents/workflows/${workflowId}/execute`, context);
    return response.data;
  }

  async pauseWorkflow(workflowId: string): Promise<{ success: boolean; message: string }> {
    const response = await this.api.post(`/agents/workflows/${workflowId}/pause`);
    return response.data;
  }

  async resumeWorkflow(workflowId: string): Promise<{ success: boolean; message: string }> {
    const response = await this.api.post(`/agents/workflows/${workflowId}/resume`);
    return response.data;
  }

  async cancelWorkflow(workflowId: string): Promise<{ success: boolean; message: string }> {
    const response = await this.api.post(`/agents/workflows/${workflowId}/cancel`);
    return response.data;
  }

  // Classificação Rápida
  async quickClassify(request: QuickClassifyRequest): Promise<QuickClassifyResult> {
    const response = await this.api.post('/agents/quick-classify', request);
    return response.data;
  }

  // Health Check
  async healthCheck(): Promise<{ status: string; agents: Record<string, string> }> {
    const response = await this.api.get('/agents/health');
    return response.data;
  }
}

export const agentsService = new AgentsService();
export default agentsService;
