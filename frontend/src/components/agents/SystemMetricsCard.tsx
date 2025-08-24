// Componente para exibir métricas do sistema de agentes
import React from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  LinearProgress,
  Chip,
  CircularProgress,
} from '@mui/material';
import {
  Speed as PerformanceIcon,
  Memory as MemoryIcon,
  Storage as CacheIcon,
  Timer as ResponseTimeIcon,
  People as AgentsIcon,
  Assignment as TasksIcon,
  AccountTree as WorkflowsIcon,
  TrendingUp as TrendingUpIcon,
} from '@mui/icons-material';
import { SystemMetrics } from '../../types/agents';

interface SystemMetricsCardProps {
  metrics: SystemMetrics;
  isLoading?: boolean;
}

const SystemMetricsCard: React.FC<SystemMetricsCardProps> = ({ metrics, isLoading }) => {
  if (isLoading) {
    return (
      <Card>
        <CardContent>
          <Box display="flex" justifyContent="center" alignItems="center" minHeight={200}>
            <CircularProgress />
          </Box>
        </CardContent>
      </Card>
    );
  }

  const getHealthColor = (percentage: number) => {
    if (percentage >= 80) return '#4caf50';
    if (percentage >= 60) return '#ff9800';
    return '#f44336';
  };

  const formatPercentage = (value: number) => `${value.toFixed(1)}%`;
  const formatTime = (seconds: number) => `${seconds.toFixed(2)}s`;

  return (
    <Grid container spacing={3}>
      {/* Métricas de Agentes */}
      <Grid item xs={12} md={6} lg={3}>
        <Card sx={{ height: '100%' }}>
          <CardContent>
            <Box display="flex" alignItems="center" mb={2}>
              <AgentsIcon color="primary" sx={{ mr: 1 }} />
              <Typography variant="h6">Agentes</Typography>
            </Box>
            
            <Typography variant="h3" color="primary" gutterBottom>
              {metrics.agent_metrics.total_agents}
            </Typography>
            
            <Box mb={2}>
              <Box display="flex" justifyContent="space-between" mb={1}>
                <Chip
                  label={`${metrics.agent_metrics.running_agents} Executando`}
                  size="small"
                  color="success"
                  variant="outlined"
                />
                <Chip
                  label={`${metrics.agent_metrics.idle_agents} Ociosos`}
                  size="small"
                  color="default"
                  variant="outlined"
                />
              </Box>
              
              {metrics.agent_metrics.error_agents > 0 && (
                <Chip
                  label={`${metrics.agent_metrics.error_agents} Com Erro`}
                  size="small"
                  color="error"
                  variant="outlined"
                />
              )}
            </Box>

            <Typography variant="body2" color="text.secondary" gutterBottom>
              Taxa de Sucesso Média
            </Typography>
            <Box display="flex" alignItems="center">
              <LinearProgress
                variant="determinate"
                value={metrics.agent_metrics.average_success_rate}
                sx={{
                  flexGrow: 1,
                  mr: 1,
                  height: 8,
                  borderRadius: 4,
                  backgroundColor: '#f0f0f0',
                  '& .MuiLinearProgress-bar': {
                    backgroundColor: getHealthColor(metrics.agent_metrics.average_success_rate),
                    borderRadius: 4,
                  },
                }}
              />
              <Typography variant="body2" fontWeight="bold">
                {formatPercentage(metrics.agent_metrics.average_success_rate)}
              </Typography>
            </Box>
          </CardContent>
        </Card>
      </Grid>

      {/* Métricas de Tarefas */}
      <Grid item xs={12} md={6} lg={3}>
        <Card sx={{ height: '100%' }}>
          <CardContent>
            <Box display="flex" alignItems="center" mb={2}>
              <TasksIcon color="secondary" sx={{ mr: 1 }} />
              <Typography variant="h6">Tarefas</Typography>
            </Box>
            
            <Typography variant="h3" color="secondary" gutterBottom>
              {metrics.agent_metrics.total_tasks_processed.toLocaleString()}
            </Typography>
            
            <Typography variant="body2" color="text.secondary">
              Total Processadas
            </Typography>
          </CardContent>
        </Card>
      </Grid>

      {/* Métricas de Workflows */}
      <Grid item xs={12} md={6} lg={3}>
        <Card sx={{ height: '100%' }}>
          <CardContent>
            <Box display="flex" alignItems="center" mb={2}>
              <WorkflowsIcon sx={{ color: '#9c27b0', mr: 1 }} />
              <Typography variant="h6">Workflows</Typography>
            </Box>
            
            <Typography variant="h3" sx={{ color: '#9c27b0' }} gutterBottom>
              {metrics.workflow_metrics.total_workflows}
            </Typography>
            
            <Box mb={2}>
              <Box display="flex" justifyContent="space-between" mb={1}>
                <Chip
                  label={`${metrics.workflow_metrics.running_workflows} Executando`}
                  size="small"
                  sx={{ backgroundColor: '#e1bee7', color: '#9c27b0' }}
                />
              </Box>
              
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Tempo Médio de Conclusão
              </Typography>
              <Typography variant="body1" fontWeight="bold">
                {formatTime(metrics.workflow_metrics.average_completion_time)}
              </Typography>
            </Box>
          </CardContent>
        </Card>
      </Grid>

      {/* Métricas de Performance */}
      <Grid item xs={12} md={6} lg={3}>
        <Card sx={{ height: '100%' }}>
          <CardContent>
            <Box display="flex" alignItems="center" mb={2}>
              <PerformanceIcon sx={{ color: '#ff5722', mr: 1 }} />
              <Typography variant="h6">Performance</Typography>
            </Box>
            
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <Box textAlign="center">
                  <MemoryIcon sx={{ color: '#ff5722', fontSize: 20 }} />
                  <Typography variant="caption" display="block" color="text.secondary">
                    CPU
                  </Typography>
                  <Typography variant="h6" color="text.primary">
                    {formatPercentage(metrics.performance_metrics.cpu_usage_percentage)}
                  </Typography>
                </Box>
              </Grid>
              
              <Grid item xs={6}>
                <Box textAlign="center">
                  <MemoryIcon sx={{ color: '#ff5722', fontSize: 20 }} />
                  <Typography variant="caption" display="block" color="text.secondary">
                    Memória
                  </Typography>
                  <Typography variant="h6" color="text.primary">
                    {formatPercentage(metrics.performance_metrics.memory_usage_percentage)}
                  </Typography>
                </Box>
              </Grid>
              
              <Grid item xs={6}>
                <Box textAlign="center">
                  <CacheIcon sx={{ color: '#ff5722', fontSize: 20 }} />
                  <Typography variant="caption" display="block" color="text.secondary">
                    Cache
                  </Typography>
                  <Typography variant="h6" color="text.primary">
                    {formatPercentage(metrics.performance_metrics.cache_hit_rate_percentage)}
                  </Typography>
                </Box>
              </Grid>
              
              <Grid item xs={6}>
                <Box textAlign="center">
                  <ResponseTimeIcon sx={{ color: '#ff5722', fontSize: 20 }} />
                  <Typography variant="caption" display="block" color="text.secondary">
                    Resposta
                  </Typography>
                  <Typography variant="h6" color="text.primary">
                    {formatTime(metrics.performance_metrics.average_response_time)}
                  </Typography>
                </Box>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      </Grid>

      {/* Card de Status Geral */}
      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Box display="flex" alignItems="center" mb={2}>
              <TrendingUpIcon color="primary" sx={{ mr: 1 }} />
              <Typography variant="h6">Status Geral do Sistema</Typography>
            </Box>
            
            <Grid container spacing={3}>
              <Grid item xs={12} md={4}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Agentes Ativos
                </Typography>
                <Box display="flex" alignItems="center" mb={1}>
                  <LinearProgress
                    variant="determinate"
                    value={(metrics.agent_metrics.running_agents / metrics.agent_metrics.total_agents) * 100}
                    sx={{
                      flexGrow: 1,
                      mr: 1,
                      height: 6,
                      borderRadius: 3,
                      backgroundColor: '#f0f0f0',
                      '& .MuiLinearProgress-bar': {
                        backgroundColor: '#4caf50',
                        borderRadius: 3,
                      },
                    }}
                  />
                  <Typography variant="body2" fontWeight="bold">
                    {((metrics.agent_metrics.running_agents / metrics.agent_metrics.total_agents) * 100).toFixed(0)}%
                  </Typography>
                </Box>
              </Grid>
              
              <Grid item xs={12} md={4}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Workflows Completados
                </Typography>
                <Box display="flex" alignItems="center" mb={1}>
                  <LinearProgress
                    variant="determinate"
                    value={(metrics.workflow_metrics.completed_workflows / Math.max(metrics.workflow_metrics.total_workflows, 1)) * 100}
                    sx={{
                      flexGrow: 1,
                      mr: 1,
                      height: 6,
                      borderRadius: 3,
                      backgroundColor: '#f0f0f0',
                      '& .MuiLinearProgress-bar': {
                        backgroundColor: '#2196f3',
                        borderRadius: 3,
                      },
                    }}
                  />
                  <Typography variant="body2" fontWeight="bold">
                    {((metrics.workflow_metrics.completed_workflows / Math.max(metrics.workflow_metrics.total_workflows, 1)) * 100).toFixed(0)}%
                  </Typography>
                </Box>
              </Grid>
              
              <Grid item xs={12} md={4}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Eficiência do Cache
                </Typography>
                <Box display="flex" alignItems="center" mb={1}>
                  <LinearProgress
                    variant="determinate"
                    value={metrics.performance_metrics.cache_hit_rate_percentage}
                    sx={{
                      flexGrow: 1,
                      mr: 1,
                      height: 6,
                      borderRadius: 3,
                      backgroundColor: '#f0f0f0',
                      '& .MuiLinearProgress-bar': {
                        backgroundColor: getHealthColor(metrics.performance_metrics.cache_hit_rate_percentage),
                        borderRadius: 3,
                      },
                    }}
                  />
                  <Typography variant="body2" fontWeight="bold">
                    {formatPercentage(metrics.performance_metrics.cache_hit_rate_percentage)}
                  </Typography>
                </Box>
              </Grid>
            </Grid>
            
            <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block' }}>
              Última atualização: {new Date(metrics.timestamp).toLocaleString('pt-BR')}
            </Typography>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );
};

export default SystemMetricsCard;
