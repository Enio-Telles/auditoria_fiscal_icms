// Componente para exibir status de um agente individual
import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  IconButton,
  Menu,
  MenuItem,
  LinearProgress,
  Tooltip,
  Grid,
} from '@mui/material';
import {
  PlayArrow as StartIcon,
  Stop as StopIcon,
  Refresh as RestartIcon,
  Delete as DeleteIcon,
  Settings as SettingsIcon,
  MoreVert as MoreIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  Schedule as PendingIcon,
  Memory as CacheIcon,
} from '@mui/icons-material';
import { Agent, STATUS_COLORS, AGENT_DESCRIPTIONS } from '../../types/agents';

interface AgentCardProps {
  agent: Agent;
  onStart: (agentId: string) => void;
  onStop: (agentId: string) => void;
  onRestart: (agentId: string) => void;
  onRemove: (agentId: string) => void;
  onConfigure: (agent: Agent) => void;
  onViewDetails: (agent: Agent) => void;
}

const AgentCard: React.FC<AgentCardProps> = ({
  agent,
  onStart,
  onStop,
  onRestart,
  onRemove,
  onConfigure,
  onViewDetails,
}) => {
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const getStatusColor = (status: string) => {
    return STATUS_COLORS[status as keyof typeof STATUS_COLORS] || '#9e9e9e';
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
        return <SuccessIcon sx={{ fontSize: 16, color: getStatusColor(status) }} />;
      case 'error':
        return <ErrorIcon sx={{ fontSize: 16, color: getStatusColor(status) }} />;
      case 'idle':
        return <PendingIcon sx={{ fontSize: 16, color: getStatusColor(status) }} />;
      default:
        return <PendingIcon sx={{ fontSize: 16, color: getStatusColor(status) }} />;
    }
  };

  const formatUptime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  const cacheHitRate = agent.metrics.cache_hits + agent.metrics.cache_misses > 0
    ? (agent.metrics.cache_hits / (agent.metrics.cache_hits + agent.metrics.cache_misses)) * 100
    : 0;

  return (
    <Card 
      sx={{ 
        height: '100%',
        transition: 'transform 0.2s, box-shadow 0.2s',
        '&:hover': {
          transform: 'translateY(-2px)',
          boxShadow: 3,
        },
        border: `2px solid ${getStatusColor(agent.status)}`,
      }}
    >
      <CardContent>
        {/* Header com nome e ações */}
        <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
          <Box>
            <Typography variant="h6" component="div" gutterBottom>
              {agent.name}
            </Typography>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              {AGENT_DESCRIPTIONS[agent.type as keyof typeof AGENT_DESCRIPTIONS] || agent.type}
            </Typography>
          </Box>
          <Box>
            <Chip
              icon={getStatusIcon(agent.status)}
              label={agent.status.toUpperCase()}
              size="small"
              sx={{
                backgroundColor: `${getStatusColor(agent.status)}20`,
                color: getStatusColor(agent.status),
                fontWeight: 'bold',
              }}
            />
            <IconButton
              size="small"
              onClick={handleMenuOpen}
              sx={{ ml: 1 }}
            >
              <MoreIcon />
            </IconButton>
          </Box>
        </Box>

        {/* Métricas principais */}
        <Grid container spacing={2} mb={2}>
          <Grid item xs={6}>
            <Box textAlign="center">
              <Typography variant="h4" color="primary">
                {agent.metrics.tasks_completed}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Tarefas Concluídas
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={6}>
            <Box textAlign="center">
              <Typography variant="h4" color="secondary">
                {agent.metrics.success_rate_percentage.toFixed(1)}%
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Taxa de Sucesso
              </Typography>
            </Box>
          </Grid>
        </Grid>

        {/* Barra de progresso da taxa de sucesso */}
        <Box mb={2}>
          <Box display="flex" justifyContent="space-between" mb={1}>
            <Typography variant="caption">Performance</Typography>
            <Typography variant="caption">
              {agent.metrics.success_rate_percentage.toFixed(1)}%
            </Typography>
          </Box>
          <LinearProgress
            variant="determinate"
            value={agent.metrics.success_rate_percentage}
            sx={{
              height: 6,
              borderRadius: 3,
              backgroundColor: '#f0f0f0',
              '& .MuiLinearProgress-bar': {
                backgroundColor: agent.metrics.success_rate_percentage >= 80 ? '#4caf50' : 
                                 agent.metrics.success_rate_percentage >= 60 ? '#ff9800' : '#f44336',
                borderRadius: 3,
              },
            }}
          />
        </Box>

        {/* Estatísticas detalhadas */}
        <Grid container spacing={1}>
          <Grid item xs={6}>
            <Tooltip title="Tempo médio de processamento">
              <Box>
                <Typography variant="caption" color="text.secondary">
                  Tempo Médio
                </Typography>
                <Typography variant="body2" fontWeight="bold">
                  {agent.metrics.average_processing_time.toFixed(2)}s
                </Typography>
              </Box>
            </Tooltip>
          </Grid>
          <Grid item xs={6}>
            <Tooltip title="Taxa de acerto do cache">
              <Box display="flex" alignItems="center">
                <CacheIcon sx={{ fontSize: 16, mr: 0.5, color: 'text.secondary' }} />
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Cache
                  </Typography>
                  <Typography variant="body2" fontWeight="bold">
                    {cacheHitRate.toFixed(1)}%
                  </Typography>
                </Box>
              </Box>
            </Tooltip>
          </Grid>
          <Grid item xs={6}>
            <Typography variant="caption" color="text.secondary">
              Falhas
            </Typography>
            <Typography variant="body2" fontWeight="bold" color="error">
              {agent.metrics.tasks_failed}
            </Typography>
          </Grid>
          <Grid item xs={6}>
            <Typography variant="caption" color="text.secondary">
              Uptime
            </Typography>
            <Typography variant="body2" fontWeight="bold">
              {formatUptime(agent.metrics.uptime_seconds)}
            </Typography>
          </Grid>
        </Grid>

        {/* Timestamp da última atividade */}
        {agent.last_heartbeat && (
          <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
            Última atividade: {new Date(agent.last_heartbeat).toLocaleString('pt-BR')}
          </Typography>
        )}

        {/* Mensagem de erro se houver */}
        {agent.error_message && (
          <Box mt={1} p={1} bgcolor="error.light" borderRadius={1}>
            <Typography variant="caption" color="error.contrastText">
              {agent.error_message}
            </Typography>
          </Box>
        )}
      </CardContent>

      {/* Menu de ações */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        {(agent.status === 'stopped' as any) || (agent.status === 'idle' as any) ? (
          <MenuItem onClick={() => { onStart(agent.id); handleMenuClose(); }}>
            <StartIcon sx={{ mr: 1 }} />
            Iniciar
          </MenuItem>
        ) : (
          <MenuItem onClick={() => { onStop(agent.id); handleMenuClose(); }}>
            <StopIcon sx={{ mr: 1 }} />
            Parar
          </MenuItem>
        )}
        
        <MenuItem onClick={() => { onRestart(agent.id); handleMenuClose(); }}>
          <RestartIcon sx={{ mr: 1 }} />
          Reiniciar
        </MenuItem>
        
        <MenuItem onClick={() => { onConfigure(agent); handleMenuClose(); }}>
          <SettingsIcon sx={{ mr: 1 }} />
          Configurar
        </MenuItem>
        
        <MenuItem onClick={() => { onViewDetails(agent); handleMenuClose(); }}>
          <SettingsIcon sx={{ mr: 1 }} />
          Ver Detalhes
        </MenuItem>
        
        <MenuItem 
          onClick={() => { onRemove(agent.id); handleMenuClose(); }}
          sx={{ color: 'error.main' }}
        >
          <DeleteIcon sx={{ mr: 1 }} />
          Remover
        </MenuItem>
      </Menu>
    </Card>
  );
};

export default AgentCard;
