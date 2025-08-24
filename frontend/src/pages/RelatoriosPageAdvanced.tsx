import React, { useState } from 'react';
import {
  Container,
  Box,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Chip,
  Alert,
  CircularProgress,
  Divider,
  Tab,
  Tabs,
  ButtonGroup,
  IconButton,
  Tooltip as MuiTooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Switch,
  FormControlLabel,
} from '@mui/material';
import {
  Assessment,
  PictureAsPdf,
  GetApp,
  TrendingUp,
  Warning,
  CheckCircle,
  Error,
  DateRange,
  Dashboard,
  Speed,
  Security,
  Timeline,
  Settings,
  Refresh,
  Share,
  Schedule,
  Notifications,
} from '@mui/icons-material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { ptBR } from 'date-fns/locale';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
} from 'recharts';
import { useQuery } from '@tanstack/react-query';
import { relatorioService } from '../services/relatorioService';

// Importar os novos componentes avançados
import ExecutiveDashboard, { ExecutiveMetrics } from '../components/reports/ExecutiveDashboard';
import PerformanceAnalytics, { PerformanceData } from '../components/reports/PerformanceAnalytics';
import ComplianceReport, { ComplianceData } from '../components/reports/ComplianceReport';

const RelatoriosPage: React.FC = () => {
  // Estados principais
  const [activeTab, setActiveTab] = useState(0);
  const [dataInicio, setDataInicio] = useState<Date | null>(null);
  const [dataFim, setDataFim] = useState<Date | null>(null);
  const [empresaSelecionada, setEmpresaSelecionada] = useState<string>('');
  const [tipoRelatorio, setTipoRelatorio] = useState<string>('executivo');
  const [configDialogOpen, setConfigDialogOpen] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(false);

  // Queries para dados básicos
  const { data: statsData, isLoading: statsLoading, refetch: refetchStats } = useQuery({
    queryKey: ['relatorio-stats', dataInicio, dataFim, empresaSelecionada],
    queryFn: () => relatorioService.getStats({
      dataInicio,
      dataFim,
      empresaId: empresaSelecionada || undefined,
    }),
  });

  const { data: classificacaoData, isLoading: classificacaoLoading } = useQuery({
    queryKey: ['classificacao-periodo', dataInicio, dataFim, empresaSelecionada],
    queryFn: () => relatorioService.getClassificacaoPorPeriodo({
      dataInicio,
      dataFim,
      empresaId: empresaSelecionada || undefined,
    }),
  });

  const { data: empresas } = useQuery({
    queryKey: ['empresas-select'],
    queryFn: () => relatorioService.getEmpresas(),
  });

  // Mock data para os novos componentes (será substituído por APIs reais)
  const executiveMetrics: ExecutiveMetrics = {
    totalProducts: statsData?.totalProdutos || 15420,
    classificationRate: 0.94,
    accuracyRate: 0.91,
    processingSpeed: 1250,
    complianceScore: 0.88,
    costSavings: 450000,
    timeReduction: 75,
    errorRate: 0.06,
    trends: {
      productsTrend: 12.5,
      accuracyTrend: 3.2,
      speedTrend: 8.7,
      complianceTrend: 5.1,
    },
    periodicData: [
      { period: 'Jan', classified: 0.89, accuracy: 0.87, speed: 0.92, compliance: 0.85 },
      { period: 'Fev', classified: 0.91, accuracy: 0.89, speed: 0.94, compliance: 0.87 },
      { period: 'Mar', classified: 0.94, accuracy: 0.91, speed: 0.96, compliance: 0.88 },
    ],
    topPerformers: [
      { category: 'Eletrônicos', value: 0.96, trend: 4.2 },
      { category: 'Têxtil', value: 0.93, trend: 2.8 },
      { category: 'Metalurgia', value: 0.89, trend: -1.5 },
      { category: 'Químicos', value: 0.87, trend: 1.2 },
    ],
    riskAreas: [
      { area: 'Classificações Pendentes', risk: 'medium', description: 'Alto volume de produtos aguardando classificação', count: 156 },
      { area: 'NCM Inconsistentes', risk: 'high', description: 'Códigos NCM com baixa precisão de classificação', count: 23 },
      { area: 'Validação Manual', risk: 'low', description: 'Itens que requerem revisão humana', count: 45 },
    ],
  };

  const performanceData: PerformanceData = {
    agentPerformance: [
      {
        agentName: 'NCM Agent',
        totalTasks: 2450,
        successRate: 0.94,
        avgResponseTime: 850,
        accuracyScore: 0.91,
        errorRate: 0.06,
        trend: 3.2,
        lastActive: '2 minutos atrás',
      },
      {
        agentName: 'CEST Agent',
        totalTasks: 1890,
        successRate: 0.89,
        avgResponseTime: 1200,
        accuracyScore: 0.87,
        errorRate: 0.11,
        trend: -1.5,
        lastActive: '5 minutos atrás',
      },
      {
        agentName: 'Expansion Agent',
        totalTasks: 3200,
        successRate: 0.97,
        avgResponseTime: 450,
        accuracyScore: 0.95,
        errorRate: 0.03,
        trend: 5.8,
        lastActive: '1 minuto atrás',
      },
    ],
    systemMetrics: [
      { timestamp: '12:00', cpu: 65, memory: 72, throughput: 85, errors: 2, activeAgents: 5 },
      { timestamp: '12:15', cpu: 58, memory: 68, throughput: 92, errors: 1, activeAgents: 5 },
      { timestamp: '12:30', cpu: 72, memory: 75, throughput: 88, errors: 3, activeAgents: 4 },
    ],
    classificationStats: [
      { category: 'Eletrônicos', total: 1250, successful: 1198, failed: 35, pending: 17, avgConfidence: 0.92, processingTime: 750 },
      { category: 'Têxtil', total: 890, successful: 831, failed: 42, pending: 17, avgConfidence: 0.88, processingTime: 920 },
      { category: 'Alimentícios', total: 2340, successful: 2198, failed: 89, pending: 53, avgConfidence: 0.95, processingTime: 680 },
    ],
    comparativeAnalysis: {
      currentPeriod: { totalProcessed: 15420, successRate: 0.94, avgTime: 850 },
      previousPeriod: { totalProcessed: 13750, successRate: 0.91, avgTime: 920 },
      improvement: { processedChange: 12.1, successRateChange: 3.3, timeChange: -7.6 },
    },
    qualityMetrics: [
      { ncmCategory: '8471.30.00', accuracy: 0.95, confidence: 0.92, humanValidation: 0.15, falsePositives: 3, falseNegatives: 2 },
      { ncmCategory: '6204.62.00', accuracy: 0.89, confidence: 0.85, humanValidation: 0.25, falsePositives: 8, falseNegatives: 5 },
      { ncmCategory: '2710.19.11', accuracy: 0.92, confidence: 0.88, humanValidation: 0.18, falsePositives: 4, falseNegatives: 3 },
    ],
  };

  const complianceData: ComplianceData = {
    overallScore: 88.5,
    complianceAreas: [
      {
        area: 'Classificação NCM',
        score: 92,
        status: 'compliant',
        issues: 3,
        description: 'Classificações NCM estão em conformidade com regulamentações federais.',
        recommendations: ['Revisar produtos com baixa confiança', 'Atualizar base de conhecimento'],
      },
      {
        area: 'Códigos CEST',
        score: 78,
        status: 'warning',
        issues: 12,
        description: 'Alguns códigos CEST precisam de revisão para conformidade estadual.',
        recommendations: ['Verificar atualizações de CEST por estado', 'Validar produtos ST'],
      },
    ],
    riskAssessment: [
      {
        riskType: 'Classificação Incorreta',
        level: 'medium',
        probability: 25,
        impact: 65,
        affectedProducts: 156,
        description: 'Risco de multas por classificação incorreta de produtos.',
        mitigationActions: ['Implementar validação dupla', 'Treinamento de equipe'],
      },
    ],
    auditTrail: [
      {
        date: '2025-08-22',
        action: 'Classificação Automática',
        user: 'Sistema IA',
        details: 'Produto XYZ classificado como NCM 8471.30.00',
        classification: 'NCM',
        impact: 'low',
      },
    ],
    ncmCompliance: [
      {
        ncmCode: '8471.30.00',
        description: 'Máquinas de processamento de dados',
        totalProducts: 245,
        correctClassifications: 234,
        incorrectClassifications: 8,
        pendingReview: 3,
        complianceRate: 0.95,
      },
    ],
    regulatoryAlerts: [
      {
        id: 'alert-001',
        severity: 'warning',
        title: 'Nova regulamentação CEST',
        description: 'Atualização nos códigos CEST para produtos eletrônicos.',
        affectedNCMs: ['8471.30.00', '8528.72.00'],
        deadline: '2025-09-15',
        status: 'open',
      },
    ],
  };

  // Cores para gráficos
  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

  // Dados para gráfico de pizza - status de classificação
  const statusData = statsData ? [
    { name: 'Classificados', value: statsData.totalClassificados, color: '#4CAF50' },
    { name: 'Pendentes', value: statsData.totalPendentes, color: '#FF9800' },
    { name: 'Com Erro', value: statsData.totalErros, color: '#F44336' },
  ] : [];

  // Função para exportar relatório
  const exportarRelatorio = async (formato: 'pdf' | 'excel') => {
    try {
      const blob = await relatorioService.exportar({
        formato,
        tipo: tipoRelatorio,
        dataInicio,
        dataFim,
        empresaId: empresaSelecionada || undefined,
      });

      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `relatorio_${tipoRelatorio}_${new Date().toISOString().split('T')[0]}.${formato === 'pdf' ? 'pdf' : 'xlsx'}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      console.log(`Relatório ${formato.toUpperCase()} exportado com sucesso`);
    } catch (error) {
      console.error('Erro ao exportar relatório');
    }
  };

  const handleRefreshAll = () => {
    refetchStats();
  };

  const TabPanel = ({ children, value, index }: any) => (
    <div hidden={value !== index} style={{ width: '100%' }}>
      {value === index && children}
    </div>
  );

  if (statsLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns} adapterLocale={ptBR}>
      <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
        {/* Header Principal */}
        <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box>
            <Typography variant="h3" fontWeight="bold" gutterBottom>
              Analytics e Relatórios Avançados
            </Typography>
            <Typography variant="h6" color="text.secondary">
              Dashboards executivos e análises completas do sistema de classificação fiscal
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
            <ButtonGroup variant="outlined">
              <Button startIcon={<Refresh />} onClick={handleRefreshAll}>
                Atualizar
              </Button>
              <Button startIcon={<Settings />} onClick={() => setConfigDialogOpen(true)}>
                Configurar
              </Button>
              <Button startIcon={<Share />}>
                Compartilhar
              </Button>
            </ButtonGroup>
          </Box>
        </Box>

        {/* Filtros Globais */}
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            <DateRange sx={{ mr: 1, verticalAlign: 'middle' }} />
            Filtros e Configurações
          </Typography>
          <Grid container spacing={3} alignItems="center">
            <Grid item xs={12} sm={6} md={3}>
              <DatePicker
                label="Data Início"
                value={dataInicio}
                onChange={setDataInicio}
                slotProps={{ textField: { fullWidth: true } }}
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <DatePicker
                label="Data Fim"
                value={dataFim}
                onChange={setDataFim}
                slotProps={{ textField: { fullWidth: true } }}
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <FormControl fullWidth>
                <InputLabel>Empresa</InputLabel>
                <Select
                  value={empresaSelecionada}
                  label="Empresa"
                  onChange={(e) => setEmpresaSelecionada(e.target.value)}
                >
                  <MenuItem value="">Todas as empresas</MenuItem>
                  {empresas?.map((empresa) => (
                    <MenuItem key={empresa.id} value={empresa.id}>
                      {empresa.nome}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <FormControl fullWidth>
                <InputLabel>Tipo de Relatório</InputLabel>
                <Select
                  value={tipoRelatorio}
                  label="Tipo de Relatório"
                  onChange={(e) => setTipoRelatorio(e.target.value)}
                >
                  <MenuItem value="executivo">Dashboard Executivo</MenuItem>
                  <MenuItem value="performance">Análise de Performance</MenuItem>
                  <MenuItem value="conformidade">Relatório de Conformidade</MenuItem>
                  <MenuItem value="operacional">Relatório Operacional</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </Paper>

        {/* Tabs de Relatórios */}
        <Paper sx={{ mb: 3 }}>
          <Tabs
            value={activeTab}
            onChange={(_, newValue) => setActiveTab(newValue)}
            variant="fullWidth"
            sx={{ borderBottom: 1, borderColor: 'divider' }}
          >
            <Tab 
              label="Dashboard Executivo" 
              icon={<Dashboard />} 
              sx={{ textTransform: 'none', fontWeight: 'medium' }}
            />
            <Tab 
              label="Performance & Analytics" 
              icon={<Speed />} 
              sx={{ textTransform: 'none', fontWeight: 'medium' }}
            />
            <Tab 
              label="Conformidade Fiscal" 
              icon={<Security />} 
              sx={{ textTransform: 'none', fontWeight: 'medium' }}
            />
            <Tab 
              label="Relatórios Clássicos" 
              icon={<Assessment />} 
              sx={{ textTransform: 'none', fontWeight: 'medium' }}
            />
          </Tabs>

          {/* Tab 1: Dashboard Executivo */}
          <TabPanel value={activeTab} index={0}>
            <Box sx={{ p: 3 }}>
              <ExecutiveDashboard 
                metrics={executiveMetrics}
                isLoading={statsLoading}
                onRefresh={handleRefreshAll}
              />
            </Box>
          </TabPanel>

          {/* Tab 2: Performance Analytics */}
          <TabPanel value={activeTab} index={1}>
            <Box sx={{ p: 3 }}>
              <PerformanceAnalytics 
                data={performanceData}
                isLoading={statsLoading}
              />
            </Box>
          </TabPanel>

          {/* Tab 3: Conformidade Fiscal */}
          <TabPanel value={activeTab} index={2}>
            <Box sx={{ p: 3 }}>
              <ComplianceReport 
                data={complianceData}
                isLoading={statsLoading}
                onExportReport={exportarRelatorio}
              />
            </Box>
          </TabPanel>

          {/* Tab 4: Relatórios Clássicos (Legado) */}
          <TabPanel value={activeTab} index={3}>
            <Box sx={{ p: 3 }}>
              <Typography variant="h5" gutterBottom>
                Relatórios Clássicos
              </Typography>
              
              {/* KPIs Básicos */}
              <Grid container spacing={3} sx={{ mb: 4 }}>
                <Grid item xs={12} sm={6} md={3}>
                  <Card>
                    <CardContent>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                        <Assessment color="primary" />
                        <Typography variant="h6" sx={{ ml: 1 }}>
                          Total de Produtos
                        </Typography>
                      </Box>
                      <Typography variant="h4" color="primary">
                        {statsData?.totalProdutos?.toLocaleString() || '0'}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Card>
                    <CardContent>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                        <CheckCircle color="success" />
                        <Typography variant="h6" sx={{ ml: 1 }}>
                          Classificados
                        </Typography>
                      </Box>
                      <Typography variant="h4" color="success.main">
                        {statsData?.totalClassificados?.toLocaleString() || '0'}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Card>
                    <CardContent>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                        <Warning color="warning" />
                        <Typography variant="h6" sx={{ ml: 1 }}>
                          Pendentes
                        </Typography>
                      </Box>
                      <Typography variant="h4" color="warning.main">
                        {statsData?.totalPendentes?.toLocaleString() || '0'}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Card>
                    <CardContent>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                        <Error color="error" />
                        <Typography variant="h6" sx={{ ml: 1 }}>
                          Com Erro
                        </Typography>
                      </Box>
                      <Typography variant="h4" color="error.main">
                        {statsData?.totalErros?.toLocaleString() || '0'}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>

              {/* Gráficos Clássicos */}
              <Grid container spacing={3}>
                {/* Gráfico de Pizza - Status */}
                <Grid item xs={12} md={6}>
                  <Paper sx={{ p: 3 }}>
                    <Typography variant="h6" gutterBottom>
                      Status das Classificações
                    </Typography>
                    <ResponsiveContainer width="100%" height={300}>
                      <PieChart>
                        <Pie
                          data={statusData}
                          cx="50%"
                          cy="50%"
                          labelLine={false}
                          label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                          outerRadius={80}
                          fill="#8884d8"
                          dataKey="value"
                        >
                          {statusData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                          ))}
                        </Pie>
                        <RechartsTooltip />
                      </PieChart>
                    </ResponsiveContainer>
                  </Paper>
                </Grid>

                {/* Gráfico de Linha - Classificações por Período */}
                <Grid item xs={12} md={6}>
                  <Paper sx={{ p: 3 }}>
                    <Typography variant="h6" gutterBottom>
                      Classificações por Período
                    </Typography>
                    {classificacaoLoading ? (
                      <Box display="flex" justifyContent="center" p={3}>
                        <CircularProgress />
                      </Box>
                    ) : (
                      <ResponsiveContainer width="100%" height={300}>
                        <LineChart data={classificacaoData}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="periodo" />
                          <YAxis />
                          <RechartsTooltip />
                          <Line 
                            type="monotone" 
                            dataKey="classificados" 
                            stroke="#4CAF50" 
                            strokeWidth={2}
                            name="Classificados"
                          />
                          <Line 
                            type="monotone" 
                            dataKey="pendentes" 
                            stroke="#FF9800" 
                            strokeWidth={2}
                            name="Pendentes"
                          />
                        </LineChart>
                      </ResponsiveContainer>
                    )}
                  </Paper>
                </Grid>
              </Grid>

              {/* Ações de Export */}
              <Paper sx={{ p: 3, mt: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Exportar Relatórios
                </Typography>
                <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                  <Button
                    variant="contained"
                    startIcon={<PictureAsPdf />}
                    onClick={() => exportarRelatorio('pdf')}
                    color="error"
                  >
                    Exportar PDF
                  </Button>
                  <Button
                    variant="contained"
                    startIcon={<GetApp />}
                    onClick={() => exportarRelatorio('excel')}
                    color="success"
                  >
                    Exportar Excel
                  </Button>
                </Box>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                  Os relatórios incluem todos os dados filtrados e gráficos correspondentes.
                </Typography>
              </Paper>

              {/* Insights */}
              {statsData && (
                <Paper sx={{ p: 3, mt: 3 }}>
                  <Typography variant="h6" gutterBottom>
                    Insights e Recomendações
                  </Typography>
                  <Grid container spacing={2}>
                    {statsData.totalErros > 0 && (
                      <Grid item xs={12}>
                        <Alert severity="warning">
                          <strong>{statsData.totalErros} produtos com erro</strong> - 
                          Revise as classificações para garantir conformidade.
                        </Alert>
                      </Grid>
                    )}
                    {statsData.totalPendentes > statsData.totalClassificados * 0.2 && (
                      <Grid item xs={12}>
                        <Alert severity="info">
                          <strong>Alto número de produtos pendentes</strong> - 
                          Execute uma nova classificação em lote para processar os itens pendentes.
                        </Alert>
                      </Grid>
                    )}
                    {statsData.acuraciaMedia && statsData.acuraciaMedia > 0.9 && (
                      <Grid item xs={12}>
                        <Alert severity="success">
                          <strong>Excelente precisão de classificação</strong> - 
                          Acurácia média de {Math.round(statsData.acuraciaMedia * 100)}%.
                        </Alert>
                      </Grid>
                    )}
                  </Grid>
                </Paper>
              )}
            </Box>
          </TabPanel>
        </Paper>

        {/* Dialog de Configurações */}
        <Dialog
          open={configDialogOpen}
          onClose={() => setConfigDialogOpen(false)}
          maxWidth="sm"
          fullWidth
        >
          <DialogTitle>
            <Settings sx={{ mr: 1, verticalAlign: 'middle' }} />
            Configurações de Relatórios
          </DialogTitle>
          <DialogContent>
            <List>
              <ListItem>
                <ListItemIcon>
                  <Refresh />
                </ListItemIcon>
                <ListItemText 
                  primary="Auto-atualização"
                  secondary="Atualizar dados automaticamente a cada 30 segundos"
                />
                <Switch
                  checked={autoRefresh}
                  onChange={(e) => setAutoRefresh(e.target.checked)}
                />
              </ListItem>
              <ListItem>
                <ListItemIcon>
                  <Notifications />
                </ListItemIcon>
                <ListItemText 
                  primary="Alertas por email"
                  secondary="Receber notificações sobre mudanças críticas"
                />
                <Switch defaultChecked />
              </ListItem>
              <ListItem>
                <ListItemIcon>
                  <Schedule />
                </ListItemIcon>
                <ListItemText 
                  primary="Relatórios agendados"
                  secondary="Envio automático de relatórios semanais"
                />
                <Switch />
              </ListItem>
            </List>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setConfigDialogOpen(false)}>Cancelar</Button>
            <Button variant="contained" onClick={() => setConfigDialogOpen(false)}>
              Salvar
            </Button>
          </DialogActions>
        </Dialog>
      </Container>
    </LocalizationProvider>
  );
};

export default RelatoriosPage;
