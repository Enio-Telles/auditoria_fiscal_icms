// Página principal do Dashboard de Agentes
import React, { useState } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  Chip,
  Alert,
  Tabs,
  Tab,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  IconButton,
  Tooltip,
  Fab,
  CircularProgress,
  Snackbar,
} from '@mui/material';
import {
  Add as AddIcon,
  Refresh as RefreshIcon,
  PlayArrow as StartAllIcon,
  Stop as StopAllIcon,
  Settings as SettingsIcon,
  Dashboard as DashboardIcon,
  Assignment as TaskIcon,
  AccountTree as WorkflowIcon,
  SmartToy as QuickClassifyIcon,
} from '@mui/icons-material';
import { useAgents } from '../hooks/useAgents';
import { AGENT_TYPES, AGENT_DESCRIPTIONS } from '../types/agents';
import AgentCard from '../components/agents/AgentCard';
import SystemMetricsCard from '../components/agents/SystemMetricsCard';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`agents-tabpanel-${index}`}
      aria-labelledby={`agents-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  );
}

const AgentsPage: React.FC = () => {
  const {
    // Estado do sistema
    systemStatus,
    systemMetrics,
    isSystemLoading,

    // Agentes
    agents,
    isAgentsLoading,

    // Tarefas
    tasks,

    // Workflows
    workflows,

    // Ações
    initializeSystem,
    shutdownSystem,
    createAgent,
    startAgent,
    stopAgent,
    removeAgent,
    restartAgent,
    refreshAgents,
    refreshSystemStatus,
    refreshMetrics,
    quickClassify,

    // Estados de carregamento
    isCreatingAgent,
    isClassifying,
  } = useAgents();

  const [currentTab, setCurrentTab] = useState(0);
  const [createAgentDialog, setCreateAgentDialog] = useState(false);
  const [quickClassifyDialog, setQuickClassifyDialog] = useState(false);
  const [selectedAgentType, setSelectedAgentType] = useState('');
  const [agentName, setAgentName] = useState('');
  const [classifyDescription, setClassifyDescription] = useState('');
  const [classifyState, setClassifyState] = useState('SP');
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'info' as any });

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setCurrentTab(newValue);
  };

  const handleCreateAgent = async () => {
    if (!selectedAgentType || !agentName) {
      setSnackbar({
        open: true,
        message: 'Por favor, preencha todos os campos',
        severity: 'error'
      });
      return;
    }

    try {
      await createAgent(selectedAgentType, { name: agentName });
      setCreateAgentDialog(false);
      setSelectedAgentType('');
      setAgentName('');
      setSnackbar({
        open: true,
        message: 'Agente criado com sucesso!',
        severity: 'success'
      });
    } catch (error) {
      setSnackbar({
        open: true,
        message: 'Erro ao criar agente',
        severity: 'error'
      });
    }
  };

  const handleQuickClassify = async () => {
    if (!classifyDescription) {
      setSnackbar({
        open: true,
        message: 'Por favor, insira uma descrição',
        severity: 'error'
      });
      return;
    }

    try {
      const result = await quickClassify({
        description: classifyDescription,
        state: classifyState,
      });

      if (result.success) {
        setSnackbar({
          open: true,
          message: `Classificação concluída: NCM ${result.summary.ncm_code}${result.summary.cest_code ? `, CEST ${result.summary.cest_code}` : ''}`,
          severity: 'success'
        });
      } else {
        setSnackbar({
          open: true,
          message: 'Erro na classificação',
          severity: 'error'
        });
      }

      setQuickClassifyDialog(false);
      setClassifyDescription('');
    } catch (error) {
      setSnackbar({
        open: true,
        message: 'Erro ao executar classificação',
        severity: 'error'
      });
    }
  };

  const handleStartAll = async () => {
    try {
      const stoppedAgents = agents.filter(agent => agent.status === 'stopped' || agent.status === 'idle');
      await Promise.all(stoppedAgents.map(agent => startAgent(agent.id)));
      setSnackbar({
        open: true,
        message: 'Todos os agentes foram iniciados',
        severity: 'success'
      });
    } catch (error) {
      setSnackbar({
        open: true,
        message: 'Erro ao iniciar agentes',
        severity: 'error'
      });
    }
  };

  const handleStopAll = async () => {
    try {
      const runningAgents = agents.filter(agent => agent.status === 'running' || agent.status === 'busy');
      await Promise.all(runningAgents.map(agent => stopAgent(agent.id)));
      setSnackbar({
        open: true,
        message: 'Todos os agentes foram parados',
        severity: 'success'
      });
    } catch (error) {
      setSnackbar({
        open: true,
        message: 'Erro ao parar agentes',
        severity: 'error'
      });
    }
  };

  const getSystemStatusColor = (): 'success' | 'warning' | 'error' | 'info' => {
    if (!systemStatus) return 'info';
    switch (systemStatus.status) {
      case 'healthy': return 'success';
      case 'degraded': return 'warning';
      case 'unhealthy': return 'error';
      default: return 'info';
    }
  };

  const convertAgentInfo = (agentInfo: any) => ({
    ...agentInfo,
    capabilities: agentInfo.capabilities || [],
    metrics: {
      ...agentInfo.metrics,
      uptime_seconds: agentInfo.metrics.uptime_seconds || 0,
    }
  });

  const runningAgents = agents.filter(agent => agent.status === 'running').length;
  const totalAgents = agents.length;

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" gutterBottom>
            🤖 Dashboard de Agentes
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Monitoramento e controle do sistema de agentes especializados
          </Typography>
        </Box>
        <Box display="flex" gap={1}>
          <Tooltip title="Atualizar dados">
            <IconButton onClick={() => {
              refreshAgents();
              refreshSystemStatus();
              refreshMetrics();
            }}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
          <Button
            variant="outlined"
            startIcon={<StartAllIcon />}
            onClick={handleStartAll}
            disabled={runningAgents === totalAgents}
          >
            Iniciar Todos
          </Button>
          <Button
            variant="outlined"
            startIcon={<StopAllIcon />}
            onClick={handleStopAll}
            disabled={runningAgents === 0}
          >
            Parar Todos
          </Button>
        </Box>
      </Box>

      {/* Status do Sistema */}
      {systemStatus && (
        <Alert
          severity={getSystemStatusColor()}
          sx={{ mb: 3 }}
          action={
            <Chip
              label={`${runningAgents}/${totalAgents} Agentes Ativos`}
              size="small"
              color={runningAgents > 0 ? 'success' : 'default'}
            />
          }
        >
          <strong>Sistema:</strong> {systemStatus.message}
        </Alert>
      )}

      {/* Tabs de Navegação */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={currentTab} onChange={handleTabChange}>
          <Tab
            icon={<DashboardIcon />}
            label="Visão Geral"
            id="agents-tab-0"
            aria-controls="agents-tabpanel-0"
          />
          <Tab
            icon={<SettingsIcon />}
            label="Agentes"
            id="agents-tab-1"
            aria-controls="agents-tabpanel-1"
          />
          <Tab
            icon={<TaskIcon />}
            label="Tarefas"
            id="agents-tab-2"
            aria-controls="agents-tabpanel-2"
          />
          <Tab
            icon={<WorkflowIcon />}
            label="Workflows"
            id="agents-tab-3"
            aria-controls="agents-tabpanel-3"
          />
        </Tabs>
      </Box>

      {/* Tab Panels */}

      {/* Visão Geral */}
      <TabPanel value={currentTab} index={0}>
        {systemMetrics ? (
          <SystemMetricsCard
            metrics={{
              ...systemMetrics,
              timestamp: new Date().toISOString()
            }}
            isLoading={isSystemLoading}
          />
        ) : (
          <Box display="flex" justifyContent="center" p={4}>
            <CircularProgress />
          </Box>
        )}
      </TabPanel>

      {/* Agentes */}
      <TabPanel value={currentTab} index={1}>
        <Grid container spacing={3}>
          {agents.map((agent) => (
            <Grid item xs={12} md={6} lg={4} key={agent.id}>
              <AgentCard
                agent={convertAgentInfo(agent) as any}
                onStart={startAgent}
                onStop={stopAgent}
                onRestart={restartAgent}
                onRemove={removeAgent}
                onConfigure={(agent) => {
                  // TODO: Implementar configuração de agente
                  setSnackbar({
                    open: true,
                    message: 'Configuração em desenvolvimento',
                    severity: 'info'
                  });
                }}
                onViewDetails={(agent) => {
                  // TODO: Implementar detalhes do agente
                  setSnackbar({
                    open: true,
                    message: 'Detalhes em desenvolvimento',
                    severity: 'info'
                  });
                }}
              />
            </Grid>
          ))}

          {agents.length === 0 && !isAgentsLoading && (
            <Grid item xs={12}>
              <Card>
                <CardContent sx={{ textAlign: 'center', py: 4 }}>
                  <Typography variant="h6" color="text.secondary">
                    Nenhum agente encontrado
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    Crie seu primeiro agente para começar
                  </Typography>
                  <Button
                    variant="contained"
                    startIcon={<AddIcon />}
                    onClick={() => setCreateAgentDialog(true)}
                  >
                    Criar Agente
                  </Button>
                </CardContent>
              </Card>
            </Grid>
          )}
        </Grid>
      </TabPanel>

      {/* Tarefas */}
      <TabPanel value={currentTab} index={2}>
        <Grid container spacing={3}>
          {tasks.slice(0, 10).map((task) => (
            <Grid item xs={12} md={6} key={task.id}>
              <Card>
                <CardContent>
                  <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                    <Typography variant="h6">{task.type}</Typography>
                    <Chip
                      label={task.status.toUpperCase()}
                      size="small"
                      color={task.status === 'completed' ? 'success' : task.status === 'failed' ? 'error' : 'default'}
                    />
                  </Box>
                  <Typography variant="body2" color="text.secondary">
                    Agente: {task.agent_id}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Criado: {new Date(task.created_at).toLocaleString('pt-BR')}
                  </Typography>
                  {(task as any).processing_time && (
                    <Typography variant="body2" color="text.secondary">
                      Tempo: {(task as any).processing_time.toFixed(2)}s
                    </Typography>
                  )}
                </CardContent>
              </Card>
            </Grid>
          ))}

          {tasks.length === 0 && (
            <Grid item xs={12}>
              <Card>
                <CardContent sx={{ textAlign: 'center', py: 4 }}>
                  <Typography variant="h6" color="text.secondary">
                    Nenhuma tarefa encontrada
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          )}
        </Grid>
      </TabPanel>

      {/* Workflows */}
      <TabPanel value={currentTab} index={3}>
        <Grid container spacing={3}>
          {workflows.map((workflow) => (
            <Grid item xs={12} md={6} key={workflow.id}>
              <Card>
                <CardContent>
                  <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                    <Typography variant="h6">{workflow.name}</Typography>
                    <Chip
                      label={workflow.status.toUpperCase()}
                      size="small"
                      color={workflow.status === 'completed' ? 'success' : workflow.status === 'failed' ? 'error' : 'default'}
                    />
                  </Box>
                  <Typography variant="body2" color="text.secondary" mb={1}>
                    {workflow.description}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Progresso: {workflow.progress_percentage.toFixed(1)}%
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Steps: {workflow.completed_steps}/{workflow.total_steps}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}

          {workflows.length === 0 && (
            <Grid item xs={12}>
              <Card>
                <CardContent sx={{ textAlign: 'center', py: 4 }}>
                  <Typography variant="h6" color="text.secondary">
                    Nenhum workflow encontrado
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          )}
        </Grid>
      </TabPanel>

      {/* FABs */}
      <Box sx={{ position: 'fixed', bottom: 16, right: 16 }}>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
          <Fab
            color="secondary"
            onClick={() => setQuickClassifyDialog(true)}
            sx={{ mb: 1 }}
          >
            <QuickClassifyIcon />
          </Fab>
          <Fab
            color="primary"
            onClick={() => setCreateAgentDialog(true)}
          >
            <AddIcon />
          </Fab>
        </Box>
      </Box>

      {/* Dialog Criar Agente */}
      <Dialog open={createAgentDialog} onClose={() => setCreateAgentDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Criar Novo Agente</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 1 }}>
            <TextField
              fullWidth
              label="Nome do Agente"
              value={agentName}
              onChange={(e) => setAgentName(e.target.value)}
              sx={{ mb: 3 }}
            />
            <FormControl fullWidth>
              <InputLabel>Tipo de Agente</InputLabel>
              <Select
                value={selectedAgentType}
                label="Tipo de Agente"
                onChange={(e) => setSelectedAgentType(e.target.value)}
              >
                {Object.entries(AGENT_TYPES).map(([key, value]) => (
                  <MenuItem key={key} value={value}>
                    <Box>
                      <Typography variant="body1">{value}</Typography>
                      <Typography variant="caption" color="text.secondary">
                        {AGENT_DESCRIPTIONS[value]}
                      </Typography>
                    </Box>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateAgentDialog(false)}>Cancelar</Button>
          <Button
            onClick={handleCreateAgent}
            variant="contained"
            disabled={isCreatingAgent}
          >
            {isCreatingAgent ? <CircularProgress size={20} /> : 'Criar'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Dialog Classificação Rápida */}
      <Dialog open={quickClassifyDialog} onClose={() => setQuickClassifyDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Classificação Rápida</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 1 }}>
            <TextField
              fullWidth
              label="Descrição do Produto"
              multiline
              rows={3}
              value={classifyDescription}
              onChange={(e) => setClassifyDescription(e.target.value)}
              sx={{ mb: 3 }}
            />
            <FormControl fullWidth>
              <InputLabel>Estado</InputLabel>
              <Select
                value={classifyState}
                label="Estado"
                onChange={(e) => setClassifyState(e.target.value)}
              >
                <MenuItem value="SP">São Paulo</MenuItem>
                <MenuItem value="RJ">Rio de Janeiro</MenuItem>
                <MenuItem value="MG">Minas Gerais</MenuItem>
                {/* Adicionar outros estados conforme necessário */}
              </Select>
            </FormControl>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setQuickClassifyDialog(false)}>Cancelar</Button>
          <Button
            onClick={handleQuickClassify}
            variant="contained"
            disabled={isClassifying}
          >
            {isClassifying ? <CircularProgress size={20} /> : 'Classificar'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar para notificações */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
      >
        <Alert
          onClose={() => setSnackbar({ ...snackbar, open: false })}
          severity={snackbar.severity}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default AgentsPage;
