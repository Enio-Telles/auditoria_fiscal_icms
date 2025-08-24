// Hook personalizado para gerenciar o estado dos agentes
import { useState, useEffect, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  agentsService,
  AgentInfo,
  AgentTask,
  WorkflowInfo,
  SystemMetrics,
  QuickClassifyRequest,
  QuickClassifyResult
} from '../services/agentsService';

export interface UseAgentsReturn {
  // Estado do sistema
  systemStatus: { status: string; message: string } | undefined;
  systemMetrics: SystemMetrics | undefined;
  isSystemLoading: boolean;
  systemError: Error | null;

  // Agentes
  agents: AgentInfo[];
  isAgentsLoading: boolean;
  agentsError: Error | null;

  // Tarefas
  tasks: AgentTask[];
  isTasksLoading: boolean;
  tasksError: Error | null;

  // Workflows
  workflows: WorkflowInfo[];
  isWorkflowsLoading: boolean;
  workflowsError: Error | null;

  // Ações do sistema
  initializeSystem: () => Promise<void>;
  shutdownSystem: () => Promise<void>;
  refreshSystemStatus: () => void;
  refreshMetrics: () => void;

  // Ações de agentes
  createAgent: (type: string, config?: Record<string, any>) => Promise<AgentInfo>;
  startAgent: (agentId: string) => Promise<void>;
  stopAgent: (agentId: string) => Promise<void>;
  removeAgent: (agentId: string) => Promise<void>;
  restartAgent: (agentId: string) => Promise<void>;
  updateAgentConfig: (agentId: string, config: Record<string, any>) => Promise<void>;
  refreshAgents: () => void;

  // Ações de tarefas
  executeTask: (agentId: string, taskType: string, taskData: Record<string, any>) => Promise<AgentTask>;
  refreshTasks: () => void;

  // Ações de workflows
  createWorkflow: (name: string, steps: any[]) => Promise<WorkflowInfo>;
  executeWorkflow: (workflowId: string, context: Record<string, any>) => Promise<{ workflow_id: string; execution_id: string }>;
  pauseWorkflow: (workflowId: string) => Promise<void>;
  resumeWorkflow: (workflowId: string) => Promise<void>;
  cancelWorkflow: (workflowId: string) => Promise<void>;
  refreshWorkflows: () => void;

  // Classificação rápida
  quickClassify: (request: QuickClassifyRequest) => Promise<QuickClassifyResult>;

  // Estados de carregamento das mutações
  isCreatingAgent: boolean;
  isExecutingTask: boolean;
  isCreatingWorkflow: boolean;
  isClassifying: boolean;
}

export const useAgents = (): UseAgentsReturn => {
  const queryClient = useQueryClient();
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Queries para dados do sistema
  const {
    data: systemStatus,
    isLoading: isSystemLoading,
    error: systemError,
    refetch: refreshSystemStatus,
  } = useQuery({
    queryKey: ['agents', 'system', 'status'],
    queryFn: agentsService.getSystemStatus,
    refetchInterval: autoRefresh ? 10000 : false, // Refresh a cada 10 segundos
    staleTime: 5000,
  });

  const {
    data: systemMetrics,
    refetch: refreshMetrics,
  } = useQuery({
    queryKey: ['agents', 'system', 'metrics'],
    queryFn: agentsService.getSystemMetrics,
    refetchInterval: autoRefresh ? 15000 : false, // Refresh a cada 15 segundos
    staleTime: 10000,
  });

  // Queries para agentes
  const {
    data: agents = [],
    isLoading: isAgentsLoading,
    error: agentsError,
    refetch: refreshAgents,
  } = useQuery({
    queryKey: ['agents', 'list'],
    queryFn: agentsService.getAgents,
    refetchInterval: autoRefresh ? 5000 : false, // Refresh a cada 5 segundos
    staleTime: 3000,
  });

  // Queries para tarefas
  const {
    data: tasks = [],
    isLoading: isTasksLoading,
    error: tasksError,
    refetch: refreshTasks,
  } = useQuery({
    queryKey: ['agents', 'tasks'],
    queryFn: agentsService.getAllTasks,
    refetchInterval: autoRefresh ? 8000 : false, // Refresh a cada 8 segundos
    staleTime: 5000,
  });

  // Queries para workflows
  const {
    data: workflows = [],
    isLoading: isWorkflowsLoading,
    error: workflowsError,
    refetch: refreshWorkflows,
  } = useQuery({
    queryKey: ['agents', 'workflows'],
    queryFn: agentsService.getWorkflows,
    refetchInterval: autoRefresh ? 12000 : false, // Refresh a cada 12 segundos
    staleTime: 8000,
  });

  // Mutações para ações do sistema
  const initializeSystemMutation = useMutation({
    mutationFn: agentsService.initializeSystem,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agents'] });
    },
  });

  const shutdownSystemMutation = useMutation({
    mutationFn: agentsService.shutdownSystem,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agents'] });
    },
  });

  // Mutações para agentes
  const createAgentMutation = useMutation({
    mutationFn: ({ type, config }: { type: string; config?: Record<string, any> }) =>
      agentsService.createAgent(type, config),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agents', 'list'] });
    },
  });

  const startAgentMutation = useMutation({
    mutationFn: agentsService.startAgent,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agents'] });
    },
  });

  const stopAgentMutation = useMutation({
    mutationFn: agentsService.stopAgent,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agents'] });
    },
  });

  const removeAgentMutation = useMutation({
    mutationFn: agentsService.removeAgent,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agents'] });
    },
  });

  const restartAgentMutation = useMutation({
    mutationFn: agentsService.restartAgent,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agents'] });
    },
  });

  const updateAgentConfigMutation = useMutation({
    mutationFn: ({ agentId, config }: { agentId: string; config: Record<string, any> }) =>
      agentsService.updateAgentConfig(agentId, config),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agents'] });
    },
  });

  // Mutações para tarefas
  const executeTaskMutation = useMutation({
    mutationFn: ({ agentId, taskType, taskData }: { agentId: string; taskType: string; taskData: Record<string, any> }) =>
      agentsService.executeTask(agentId, taskType, taskData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agents', 'tasks'] });
    },
  });

  // Mutações para workflows
  const createWorkflowMutation = useMutation({
    mutationFn: ({ name, steps }: { name: string; steps: any[] }) =>
      agentsService.createWorkflow(name, steps),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agents', 'workflows'] });
    },
  });

  const executeWorkflowMutation = useMutation({
    mutationFn: ({ workflowId, context }: { workflowId: string; context: Record<string, any> }) =>
      agentsService.executeWorkflow(workflowId, context),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agents', 'workflows'] });
    },
  });

  const pauseWorkflowMutation = useMutation({
    mutationFn: agentsService.pauseWorkflow,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agents', 'workflows'] });
    },
  });

  const resumeWorkflowMutation = useMutation({
    mutationFn: agentsService.resumeWorkflow,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agents', 'workflows'] });
    },
  });

  const cancelWorkflowMutation = useMutation({
    mutationFn: agentsService.cancelWorkflow,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agents', 'workflows'] });
    },
  });

  // Mutação para classificação rápida
  const quickClassifyMutation = useMutation({
    mutationFn: agentsService.quickClassify,
  });

  // Funções wrapper para as ações
  const initializeSystem = useCallback(async () => {
    await initializeSystemMutation.mutateAsync();
  }, [initializeSystemMutation]);

  const shutdownSystem = useCallback(async () => {
    await shutdownSystemMutation.mutateAsync();
  }, [shutdownSystemMutation]);

  const createAgent = useCallback(async (type: string, config?: Record<string, any>) => {
    return await createAgentMutation.mutateAsync({ type, config });
  }, [createAgentMutation]);

  const startAgent = useCallback(async (agentId: string) => {
    await startAgentMutation.mutateAsync(agentId);
  }, [startAgentMutation]);

  const stopAgent = useCallback(async (agentId: string) => {
    await stopAgentMutation.mutateAsync(agentId);
  }, [stopAgentMutation]);

  const removeAgent = useCallback(async (agentId: string) => {
    await removeAgentMutation.mutateAsync(agentId);
  }, [removeAgentMutation]);

  const restartAgent = useCallback(async (agentId: string) => {
    await restartAgentMutation.mutateAsync(agentId);
  }, [restartAgentMutation]);

  const updateAgentConfig = useCallback(async (agentId: string, config: Record<string, any>) => {
    await updateAgentConfigMutation.mutateAsync({ agentId, config });
  }, [updateAgentConfigMutation]);

  const executeTask = useCallback(async (agentId: string, taskType: string, taskData: Record<string, any>) => {
    return await executeTaskMutation.mutateAsync({ agentId, taskType, taskData });
  }, [executeTaskMutation]);

  const createWorkflow = useCallback(async (name: string, steps: any[]) => {
    return await createWorkflowMutation.mutateAsync({ name, steps });
  }, [createWorkflowMutation]);

  const executeWorkflow = useCallback(async (workflowId: string, context: Record<string, any>) => {
    return await executeWorkflowMutation.mutateAsync({ workflowId, context });
  }, [executeWorkflowMutation]);

  const pauseWorkflow = useCallback(async (workflowId: string) => {
    await pauseWorkflowMutation.mutateAsync(workflowId);
  }, [pauseWorkflowMutation]);

  const resumeWorkflow = useCallback(async (workflowId: string) => {
    await resumeWorkflowMutation.mutateAsync(workflowId);
  }, [resumeWorkflowMutation]);

  const cancelWorkflow = useCallback(async (workflowId: string) => {
    await cancelWorkflowMutation.mutateAsync(workflowId);
  }, [cancelWorkflowMutation]);

  const quickClassify = useCallback(async (request: QuickClassifyRequest) => {
    return await quickClassifyMutation.mutateAsync(request);
  }, [quickClassifyMutation]);

  return {
    // Estado do sistema
    systemStatus,
    systemMetrics,
    isSystemLoading,
    systemError,

    // Agentes
    agents,
    isAgentsLoading,
    agentsError,

    // Tarefas
    tasks,
    isTasksLoading,
    tasksError,

    // Workflows
    workflows,
    isWorkflowsLoading,
    workflowsError,

    // Ações do sistema
    initializeSystem,
    shutdownSystem,
    refreshSystemStatus,
    refreshMetrics,

    // Ações de agentes
    createAgent,
    startAgent,
    stopAgent,
    removeAgent,
    restartAgent,
    updateAgentConfig,
    refreshAgents,

    // Ações de tarefas
    executeTask,
    refreshTasks,

    // Ações de workflows
    createWorkflow,
    executeWorkflow,
    pauseWorkflow,
    resumeWorkflow,
    cancelWorkflow,
    refreshWorkflows,

    // Classificação rápida
    quickClassify,

    // Estados de carregamento das mutações
    isCreatingAgent: createAgentMutation.isPending,
    isExecutingTask: executeTaskMutation.isPending,
    isCreatingWorkflow: createWorkflowMutation.isPending,
    isClassifying: quickClassifyMutation.isPending,
  };
};
