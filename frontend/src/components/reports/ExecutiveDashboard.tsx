import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  IconButton,
  Chip,
  LinearProgress,
  Tooltip,
  Alert,
  Button,
  Menu,
  MenuItem,
  Divider,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  Info,
  Speed,
  Assignment,
  Business,
  PieChart,
  Timeline,
  MoreVert,
  Refresh,
  OpenInNew,
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart as RechartsPieChart,
  Pie,
  Cell,
  RadialBarChart,
  RadialBar,
  Legend,
} from 'recharts';

export interface ExecutiveMetrics {
  totalProducts: number;
  classificationRate: number;
  accuracyRate: number;
  processingSpeed: number;
  complianceScore: number;
  costSavings: number;
  timeReduction: number;
  errorRate: number;
  trends: {
    productsTrend: number;
    accuracyTrend: number;
    speedTrend: number;
    complianceTrend: number;
  };
  periodicData: Array<{
    period: string;
    classified: number;
    accuracy: number;
    speed: number;
    compliance: number;
  }>;
  topPerformers: Array<{
    category: string;
    value: number;
    trend: number;
  }>;
  riskAreas: Array<{
    area: string;
    risk: 'low' | 'medium' | 'high';
    description: string;
    count: number;
  }>;
}

interface ExecutiveDashboardProps {
  metrics: ExecutiveMetrics;
  isLoading?: boolean;
  onRefresh?: () => void;
}

const ExecutiveDashboard: React.FC<ExecutiveDashboardProps> = ({
  metrics,
  isLoading = false,
  onRefresh,
}) => {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  const formatNumber = (num: number): string => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  };

  const formatPercentage = (num: number): string => `${(num * 100).toFixed(1)}%`;

  const getTrendIcon = (trend: number) => {
    return trend > 0 ? (
      <TrendingUp sx={{ color: 'success.main', fontSize: 20 }} />
    ) : (
      <TrendingDown sx={{ color: 'error.main', fontSize: 20 }} />
    );
  };

  const getTrendColor = (trend: number): 'success' | 'error' | 'warning' => {
    if (trend > 5) return 'success';
    if (trend < -5) return 'error';
    return 'warning';
  };

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'high': return '#f44336';
      case 'medium': return '#ff9800';
      case 'low': return '#4caf50';
      default: return '#757575';
    }
  };

  const kpiCards = [
    {
      title: 'Produtos Processados',
      value: formatNumber(metrics.totalProducts),
      subtitle: 'Total no período',
      trend: metrics.trends.productsTrend,
      icon: <Assignment color="primary" />,
      color: 'primary',
    },
    {
      title: 'Taxa de Classificação',
      value: formatPercentage(metrics.classificationRate),
      subtitle: 'Sucesso automático',
      trend: metrics.trends.accuracyTrend,
      icon: <Speed color="secondary" />,
      color: 'secondary',
    },
    {
      title: 'Acurácia Geral',
      value: formatPercentage(metrics.accuracyRate),
      subtitle: 'Precisão validada',
      trend: metrics.trends.accuracyTrend,
      icon: <PieChart sx={{ color: 'success.main' }} />,
      color: 'success',
    },
    {
      title: 'Conformidade Fiscal',
      value: formatPercentage(metrics.complianceScore),
      subtitle: 'Score de conformidade',
      trend: metrics.trends.complianceTrend,
      icon: <Business sx={{ color: 'warning.main' }} />,
      color: 'warning',
    },
  ];

  const businessImpactData = [
    {
      name: 'Economia de Custo',
      value: metrics.costSavings,
      fill: '#8884d8',
      target: 100000,
    },
    {
      name: 'Redução de Tempo',
      value: metrics.timeReduction,
      fill: '#82ca9d',
      target: 80,
    },
  ];

  return (
    <Box>
      {/* Header com ações */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" fontWeight="bold" gutterBottom>
            Dashboard Executivo
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Visão estratégica do sistema de classificação fiscal
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={onRefresh}
            disabled={isLoading}
          >
            Atualizar
          </Button>
          <IconButton
            onClick={(e) => setAnchorEl(e.currentTarget)}
            size="small"
          >
            <MoreVert />
          </IconButton>
          <Menu
            anchorEl={anchorEl}
            open={Boolean(anchorEl)}
            onClose={() => setAnchorEl(null)}
          >
            <MenuItem onClick={() => setAnchorEl(null)}>
              <OpenInNew sx={{ mr: 1 }} /> Exportar Dashboard
            </MenuItem>
            <MenuItem onClick={() => setAnchorEl(null)}>
              <Timeline sx={{ mr: 1 }} /> Análise Detalhada
            </MenuItem>
          </Menu>
        </Box>
      </Box>

      {/* Alertas de Alto Nível */}
      {metrics.errorRate > 0.1 && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          <strong>Taxa de erro elevada:</strong> {formatPercentage(metrics.errorRate)} dos produtos
          apresentaram problemas na classificação. Recomenda-se revisão dos parâmetros.
        </Alert>
      )}

      {/* KPIs Principais */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {kpiCards.map((kpi, index) => (
          <Grid item xs={12} sm={6} md={3} key={index}>
            <Card sx={{ height: '100%', position: 'relative', overflow: 'visible' }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  {kpi.icon}
                  <Box sx={{ ml: 'auto', display: 'flex', alignItems: 'center' }}>
                    {getTrendIcon(kpi.trend)}
                    <Chip
                      label={`${kpi.trend > 0 ? '+' : ''}${kpi.trend.toFixed(1)}%`}
                      size="small"
                      color={getTrendColor(kpi.trend)}
                      variant="outlined"
                      sx={{ ml: 0.5 }}
                    />
                  </Box>
                </Box>
                <Typography variant="h4" fontWeight="bold" color={`${kpi.color}.main`}>
                  {kpi.value}
                </Typography>
                <Typography variant="h6" color="text.primary" sx={{ mt: 0.5 }}>
                  {kpi.title}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {kpi.subtitle}
                </Typography>
              </CardContent>
              {isLoading && (
                <LinearProgress
                  sx={{
                    position: 'absolute',
                    bottom: 0,
                    left: 0,
                    right: 0,
                    borderBottomLeftRadius: 4,
                    borderBottomRightRadius: 4,
                  }}
                />
              )}
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Gráficos Analíticos */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {/* Tendência Temporal */}
        <Grid item xs={12} lg={8}>
          <Paper sx={{ p: 3, height: 400 }}>
            <Typography variant="h6" gutterBottom>
              Tendências de Performance
            </Typography>
            <ResponsiveContainer width="100%" height="90%">
              <AreaChart data={metrics.periodicData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="period" />
                <YAxis />
                <RechartsTooltip
                  formatter={(value, name) => [
                    typeof value === 'number' ? formatPercentage(value) : value,
                    name === 'classified' ? 'Classificados' :
                    name === 'accuracy' ? 'Acurácia' :
                    name === 'speed' ? 'Velocidade' : 'Conformidade'
                  ]}
                />
                <Area
                  type="monotone"
                  dataKey="accuracy"
                  stackId="1"
                  stroke="#8884d8"
                  fill="#8884d8"
                  fillOpacity={0.6}
                />
                <Area
                  type="monotone"
                  dataKey="compliance"
                  stackId="1"
                  stroke="#82ca9d"
                  fill="#82ca9d"
                  fillOpacity={0.6}
                />
              </AreaChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* Indicador Radial de Conformidade */}
        <Grid item xs={12} lg={4}>
          <Paper sx={{ p: 3, height: 400 }}>
            <Typography variant="h6" gutterBottom>
              Score de Conformidade
            </Typography>
            <ResponsiveContainer width="100%" height="90%">
              <RadialBarChart cx="50%" cy="50%" innerRadius="40%" outerRadius="90%" data={[
                { name: 'Conformidade', value: metrics.complianceScore * 100, fill: '#8884d8' }
              ]}>
                <RadialBar
                  dataKey="value"
                  cornerRadius={4}
                  fill="#8884d8"
                />
                <Legend
                  iconSize={18}
                  layout="vertical"
                  verticalAlign="middle"
                  wrapperStyle={{
                    lineHeight: '40px'
                  }}
                />
              </RadialBarChart>
            </ResponsiveContainer>
            <Box sx={{ textAlign: 'center', mt: 2 }}>
              <Typography variant="h4" color="primary">
                {formatPercentage(metrics.complianceScore)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Score geral de conformidade fiscal
              </Typography>
            </Box>
          </Paper>
        </Grid>
      </Grid>

      {/* Top Performers e Áreas de Risco */}
      <Grid container spacing={3}>
        {/* Top Performers */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Categorias com Melhor Performance
            </Typography>
            <Box sx={{ mt: 2 }}>
              {metrics.topPerformers.map((performer, index) => (
                <Box key={index} sx={{ mb: 2 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.5 }}>
                    <Typography variant="body1">{performer.category}</Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Typography variant="body2" color="text.secondary" sx={{ mr: 1 }}>
                        {formatPercentage(performer.value)}
                      </Typography>
                      {getTrendIcon(performer.trend)}
                    </Box>
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={performer.value * 100}
                    sx={{ height: 8, borderRadius: 1 }}
                  />
                </Box>
              ))}
            </Box>
          </Paper>
        </Grid>

        {/* Áreas de Risco */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Áreas de Atenção
            </Typography>
            <Box sx={{ mt: 2 }}>
              {metrics.riskAreas.map((risk, index) => (
                <Card key={index} sx={{ mb: 2, border: `2px solid ${getRiskColor(risk.risk)}` }}>
                  <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                      <Typography variant="subtitle1" fontWeight="medium">
                        {risk.area}
                      </Typography>
                      <Chip
                        label={risk.risk.toUpperCase()}
                        size="small"
                        sx={{
                          backgroundColor: getRiskColor(risk.risk),
                          color: 'white',
                          fontWeight: 'bold',
                        }}
                      />
                    </Box>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      {risk.description}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {risk.count} itens afetados
                    </Typography>
                  </CardContent>
                </Card>
              ))}
            </Box>
          </Paper>
        </Grid>
      </Grid>

      {/* Impacto nos Negócios */}
      <Grid container spacing={3} sx={{ mt: 2 }}>
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Impacto nos Negócios
            </Typography>
            <Grid container spacing={3} sx={{ mt: 1 }}>
              <Grid item xs={12} md={4}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="h3" color="success.main" fontWeight="bold">
                    R$ {formatNumber(metrics.costSavings)}
                  </Typography>
                  <Typography variant="body1" color="text.secondary">
                    Economia de Custos (anual)
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} md={4}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="h3" color="primary.main" fontWeight="bold">
                    {metrics.timeReduction}%
                  </Typography>
                  <Typography variant="body1" color="text.secondary">
                    Redução de Tempo de Processo
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} md={4}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="h3" color="secondary.main" fontWeight="bold">
                    {formatNumber(metrics.processingSpeed)}/h
                  </Typography>
                  <Typography variant="body1" color="text.secondary">
                    Produtos Processados por Hora
                  </Typography>
                </Box>
              </Grid>
            </Grid>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default ExecutiveDashboard;
