import React, { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  Tab,
  Tabs,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Chip,
  LinearProgress,
  IconButton,
  Tooltip,
  ButtonGroup,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
} from '@mui/material';
import {
  Visibility,
  Download,
  TrendingUp,
  TrendingDown,
  Speed,
  CheckCircle,
  Assessment,
  CompareArrows,
  FilterList,
  Timeline,
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  ComposedChart,
  Bar,
  Area,
  AreaChart,
  ScatterChart,
  Scatter,
  ZAxis,
} from 'recharts';

export interface PerformanceData {
  agentPerformance: Array<{
    agentName: string;
    totalTasks: number;
    successRate: number;
    avgResponseTime: number;
    accuracyScore: number;
    errorRate: number;
    trend: number;
    lastActive: string;
  }>;
  systemMetrics: Array<{
    timestamp: string;
    cpu: number;
    memory: number;
    throughput: number;
    errors: number;
    activeAgents: number;
  }>;
  classificationStats: Array<{
    category: string;
    total: number;
    successful: number;
    failed: number;
    pending: number;
    avgConfidence: number;
    processingTime: number;
  }>;
  comparativeAnalysis: {
    currentPeriod: {
      totalProcessed: number;
      successRate: number;
      avgTime: number;
    };
    previousPeriod: {
      totalProcessed: number;
      successRate: number;
      avgTime: number;
    };
    improvement: {
      processedChange: number;
      successRateChange: number;
      timeChange: number;
    };
  };
  qualityMetrics: Array<{
    ncmCategory: string;
    accuracy: number;
    confidence: number;
    humanValidation: number;
    falsePositives: number;
    falseNegatives: number;
  }>;
}

interface PerformanceAnalyticsProps {
  data: PerformanceData;
  isLoading?: boolean;
}

const PerformanceAnalytics: React.FC<PerformanceAnalyticsProps> = ({
  data,
  isLoading = false,
}) => {
  const [activeTab, setActiveTab] = useState(0);
  const [agentPage, setAgentPage] = useState(0);
  const [agentRowsPerPage, setAgentRowsPerPage] = useState(10);
  const [timeRange, setTimeRange] = useState('24h');

  const formatPercentage = (value: number) => `${(value * 100).toFixed(1)}%`;
  const formatTime = (ms: number) => `${(ms / 1000).toFixed(2)}s`;
  const formatNumber = (num: number) => num.toLocaleString();

  const getStatusColor = (rate: number) => {
    if (rate >= 0.95) return 'success';
    if (rate >= 0.85) return 'warning';
    return 'error';
  };

  const getTrendIcon = (trend: number) => {
    return trend > 0 ? (
      <TrendingUp sx={{ color: 'success.main', fontSize: 16 }} />
    ) : (
      <TrendingDown sx={{ color: 'error.main', fontSize: 16 }} />
    );
  };

  const TabPanel = ({ children, value, index }: any) => (
    <div hidden={value !== index} style={{ paddingTop: 16 }}>
      {value === index && children}
    </div>
  );

  return (
    <Box>
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h5" fontWeight="bold">
          Análise de Performance
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Período</InputLabel>
            <Select
              value={timeRange}
              label="Período"
              onChange={(e) => setTimeRange(e.target.value)}
            >
              <MenuItem value="1h">1 Hora</MenuItem>
              <MenuItem value="24h">24 Horas</MenuItem>
              <MenuItem value="7d">7 Dias</MenuItem>
              <MenuItem value="30d">30 Dias</MenuItem>
            </Select>
          </FormControl>
          <ButtonGroup variant="outlined" size="small">
            <Button startIcon={<Download />}>Exportar</Button>
            <Button startIcon={<FilterList />}>Filtros</Button>
          </ButtonGroup>
        </Box>
      </Box>

      {/* Comparação de Períodos */}
      <Alert severity="info" sx={{ mb: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%' }}>
          <Box>
            <strong>Comparação com período anterior:</strong>
            <Chip
              label={`${data.comparativeAnalysis.improvement.processedChange > 0 ? '+' : ''}${data.comparativeAnalysis.improvement.processedChange.toFixed(1)}% produtos`}
              color={data.comparativeAnalysis.improvement.processedChange > 0 ? 'success' : 'error'}
              size="small"
              sx={{ ml: 1 }}
            />
            <Chip
              label={`${data.comparativeAnalysis.improvement.successRateChange > 0 ? '+' : ''}${data.comparativeAnalysis.improvement.successRateChange.toFixed(1)}% taxa de sucesso`}
              color={data.comparativeAnalysis.improvement.successRateChange > 0 ? 'success' : 'error'}
              size="small"
              sx={{ ml: 1 }}
            />
          </Box>
        </Box>
      </Alert>

      <Paper sx={{ p: 0 }}>
        <Tabs
          value={activeTab}
          onChange={(_, newValue) => setActiveTab(newValue)}
          sx={{ borderBottom: 1, borderColor: 'divider', px: 2 }}
        >
          <Tab label="Agentes" icon={<Assessment />} />
          <Tab label="Sistema" icon={<Speed />} />
          <Tab label="Classificações" icon={<CheckCircle />} />
          <Tab label="Qualidade" icon={<Timeline />} />
        </Tabs>

        {/* Tab 1: Performance dos Agentes */}
        <TabPanel value={activeTab} index={0}>
          <Box sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Performance Individual dos Agentes
            </Typography>

            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Agente</TableCell>
                    <TableCell align="right">Tarefas</TableCell>
                    <TableCell align="right">Taxa de Sucesso</TableCell>
                    <TableCell align="right">Tempo Médio</TableCell>
                    <TableCell align="right">Acurácia</TableCell>
                    <TableCell align="right">Tendência</TableCell>
                    <TableCell align="center">Ações</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {data.agentPerformance
                    .slice(agentPage * agentRowsPerPage, agentPage * agentRowsPerPage + agentRowsPerPage)
                    .map((agent, index) => (
                      <TableRow key={index} hover>
                        <TableCell>
                          <Box>
                            <Typography variant="subtitle2">{agent.agentName}</Typography>
                            <Typography variant="caption" color="text.secondary">
                              Última atividade: {agent.lastActive}
                            </Typography>
                          </Box>
                        </TableCell>
                        <TableCell align="right">
                          <Typography variant="body2" fontWeight="medium">
                            {formatNumber(agent.totalTasks)}
                          </Typography>
                        </TableCell>
                        <TableCell align="right">
                          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end' }}>
                            <Chip
                              label={formatPercentage(agent.successRate)}
                              color={getStatusColor(agent.successRate)}
                              size="small"
                              variant="outlined"
                            />
                          </Box>
                        </TableCell>
                        <TableCell align="right">
                          {formatTime(agent.avgResponseTime)}
                        </TableCell>
                        <TableCell align="right">
                          <Box sx={{ width: 100 }}>
                            <LinearProgress
                              variant="determinate"
                              value={agent.accuracyScore * 100}
                              color={getStatusColor(agent.accuracyScore)}
                              sx={{ height: 8, borderRadius: 1 }}
                            />
                            <Typography variant="caption" color="text.secondary">
                              {formatPercentage(agent.accuracyScore)}
                            </Typography>
                          </Box>
                        </TableCell>
                        <TableCell align="right">
                          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end' }}>
                            {getTrendIcon(agent.trend)}
                            <Typography variant="caption" sx={{ ml: 0.5 }}>
                              {agent.trend > 0 ? '+' : ''}{agent.trend.toFixed(1)}%
                            </Typography>
                          </Box>
                        </TableCell>
                        <TableCell align="center">
                          <Tooltip title="Ver detalhes">
                            <IconButton size="small">
                              <Visibility />
                            </IconButton>
                          </Tooltip>
                        </TableCell>
                      </TableRow>
                    ))}
                </TableBody>
              </Table>
            </TableContainer>

            <TablePagination
              component="div"
              count={data.agentPerformance.length}
              page={agentPage}
              onPageChange={(_, newPage) => setAgentPage(newPage)}
              rowsPerPage={agentRowsPerPage}
              onRowsPerPageChange={(e) => setAgentRowsPerPage(parseInt(e.target.value, 10))}
              labelRowsPerPage="Itens por página:"
            />
          </Box>
        </TabPanel>

        {/* Tab 2: Métricas do Sistema */}
        <TabPanel value={activeTab} index={1}>
          <Box sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Métricas de Sistema em Tempo Real
            </Typography>

            <Grid container spacing={3}>
              <Grid item xs={12} lg={8}>
                <Paper sx={{ p: 2, height: 400 }}>
                  <Typography variant="subtitle1" gutterBottom>
                    Performance do Sistema
                  </Typography>
                  <ResponsiveContainer width="100%" height="90%">
                    <ComposedChart data={data.systemMetrics}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="timestamp" />
                      <YAxis yAxisId="left" />
                      <YAxis yAxisId="right" orientation="right" />
                      <RechartsTooltip />
                      <Bar yAxisId="left" dataKey="throughput" fill="#8884d8" name="Throughput" />
                      <Line yAxisId="right" type="monotone" dataKey="cpu" stroke="#82ca9d" name="CPU %" />
                      <Line yAxisId="right" type="monotone" dataKey="memory" stroke="#ffc658" name="Memória %" />
                    </ComposedChart>
                  </ResponsiveContainer>
                </Paper>
              </Grid>

              <Grid item xs={12} lg={4}>
                <Paper sx={{ p: 2, height: 400 }}>
                  <Typography variant="subtitle1" gutterBottom>
                    Status Atual
                  </Typography>
                  <Box sx={{ mt: 3 }}>
                    {[
                      { label: 'CPU', value: data.systemMetrics[data.systemMetrics.length - 1]?.cpu || 0, unit: '%' },
                      { label: 'Memória', value: data.systemMetrics[data.systemMetrics.length - 1]?.memory || 0, unit: '%' },
                      { label: 'Throughput', value: data.systemMetrics[data.systemMetrics.length - 1]?.throughput || 0, unit: '/min' },
                      { label: 'Agentes Ativos', value: data.systemMetrics[data.systemMetrics.length - 1]?.activeAgents || 0, unit: '' },
                    ].map((metric, index) => (
                      <Box key={index} sx={{ mb: 3 }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                          <Typography variant="body2">{metric.label}</Typography>
                          <Typography variant="body2" fontWeight="bold">
                            {metric.value}{metric.unit}
                          </Typography>
                        </Box>
                        <LinearProgress
                          variant="determinate"
                          value={metric.label === 'Agentes Ativos' ? (metric.value / 5) * 100 : metric.value}
                          color={metric.value > 80 ? 'error' : metric.value > 60 ? 'warning' : 'success'}
                          sx={{ height: 8, borderRadius: 1 }}
                        />
                      </Box>
                    ))}
                  </Box>
                </Paper>
              </Grid>
            </Grid>
          </Box>
        </TabPanel>

        {/* Tab 3: Estatísticas de Classificação */}
        <TabPanel value={activeTab} index={2}>
          <Box sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Análise de Classificações por Categoria
            </Typography>

            <Grid container spacing={3}>
              <Grid item xs={12} lg={6}>
                <Paper sx={{ p: 2, height: 400 }}>
                  <Typography variant="subtitle1" gutterBottom>
                    Volume por Categoria
                  </Typography>
                  <ResponsiveContainer width="100%" height="90%">
                    <AreaChart data={data.classificationStats}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="category" />
                      <YAxis />
                      <RechartsTooltip />
                      <Area
                        type="monotone"
                        dataKey="successful"
                        stackId="1"
                        stroke="#82ca9d"
                        fill="#82ca9d"
                      />
                      <Area
                        type="monotone"
                        dataKey="failed"
                        stackId="1"
                        stroke="#ffc658"
                        fill="#ffc658"
                      />
                      <Area
                        type="monotone"
                        dataKey="pending"
                        stackId="1"
                        stroke="#ff7300"
                        fill="#ff7300"
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </Paper>
              </Grid>

              <Grid item xs={12} lg={6}>
                <Paper sx={{ p: 2, height: 400 }}>
                  <Typography variant="subtitle1" gutterBottom>
                    Confiança vs Tempo de Processamento
                  </Typography>
                  <ResponsiveContainer width="100%" height="90%">
                    <ScatterChart data={data.classificationStats}>
                      <CartesianGrid />
                      <XAxis type="number" dataKey="avgConfidence" name="Confiança" />
                      <YAxis type="number" dataKey="processingTime" name="Tempo (ms)" />
                      <ZAxis type="number" dataKey="total" range={[60, 400]} />
                      <RechartsTooltip cursor={{ strokeDasharray: '3 3' }} />
                      <Scatter dataKey="total" fill="#8884d8" />
                    </ScatterChart>
                  </ResponsiveContainer>
                </Paper>
              </Grid>
            </Grid>

            <Box sx={{ mt: 3 }}>
              <Typography variant="subtitle1" gutterBottom>
                Resumo por Categoria
              </Typography>
              <Grid container spacing={2}>
                {data.classificationStats.map((stat, index) => (
                  <Grid item xs={12} sm={6} md={4} key={index}>
                    <Card>
                      <CardContent>
                        <Typography variant="h6" color="primary">
                          {stat.category}
                        </Typography>
                        <Box sx={{ mt: 2 }}>
                          <Typography variant="body2" color="text.secondary">
                            Total: {formatNumber(stat.total)}
                          </Typography>
                          <Typography variant="body2" color="success.main">
                            Sucesso: {formatNumber(stat.successful)} ({formatPercentage(stat.successful / stat.total)})
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            Tempo médio: {formatTime(stat.processingTime)}
                          </Typography>
                          <Box sx={{ mt: 1 }}>
                            <LinearProgress
                              variant="determinate"
                              value={(stat.successful / stat.total) * 100}
                              color="success"
                              sx={{ height: 6, borderRadius: 1 }}
                            />
                          </Box>
                        </Box>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            </Box>
          </Box>
        </TabPanel>

        {/* Tab 4: Métricas de Qualidade */}
        <TabPanel value={activeTab} index={3}>
          <Box sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Análise de Qualidade e Validação
            </Typography>

            <Grid container spacing={3}>
              <Grid item xs={12}>
                <TableContainer component={Paper}>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Categoria NCM</TableCell>
                        <TableCell align="right">Acurácia</TableCell>
                        <TableCell align="right">Confiança Média</TableCell>
                        <TableCell align="right">Validação Humana</TableCell>
                        <TableCell align="right">Falsos Positivos</TableCell>
                        <TableCell align="right">Falsos Negativos</TableCell>
                        <TableCell align="center">Status</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {data.qualityMetrics.map((metric, index) => (
                        <TableRow key={index} hover>
                          <TableCell>
                            <Typography variant="subtitle2">{metric.ncmCategory}</Typography>
                          </TableCell>
                          <TableCell align="right">
                            <Chip
                              label={formatPercentage(metric.accuracy)}
                              color={getStatusColor(metric.accuracy)}
                              size="small"
                            />
                          </TableCell>
                          <TableCell align="right">
                            {formatPercentage(metric.confidence)}
                          </TableCell>
                          <TableCell align="right">
                            {formatPercentage(metric.humanValidation)}
                          </TableCell>
                          <TableCell align="right">
                            <Typography color={metric.falsePositives > 5 ? 'error.main' : 'text.primary'}>
                              {metric.falsePositives}
                            </Typography>
                          </TableCell>
                          <TableCell align="right">
                            <Typography color={metric.falseNegatives > 5 ? 'error.main' : 'text.primary'}>
                              {metric.falseNegatives}
                            </Typography>
                          </TableCell>
                          <TableCell align="center">
                            <Chip
                              label={metric.accuracy > 0.9 ? 'Excelente' : metric.accuracy > 0.8 ? 'Bom' : 'Precisa Melhoria'}
                              color={metric.accuracy > 0.9 ? 'success' : metric.accuracy > 0.8 ? 'warning' : 'error'}
                              size="small"
                            />
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Grid>
            </Grid>
          </Box>
        </TabPanel>
      </Paper>
    </Box>
  );
};

export default PerformanceAnalytics;
