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
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
} from 'recharts';
import { useQuery } from '@tanstack/react-query';
import { relatorioService } from '../services/relatorioService';
import { useSnackbar } from 'notistack';
import { ClassificacaoStatus } from '../types';

const RelatoriosPage: React.FC = () => {
  const { enqueueSnackbar } = useSnackbar();
  
  // Estados para filtros
  const [dataInicio, setDataInicio] = useState<Date | null>(null);
  const [dataFim, setDataFim] = useState<Date | null>(null);
  const [empresaSelecionada, setEmpresaSelecionada] = useState<string>('');
  const [tipoRelatorio, setTipoRelatorio] = useState<string>('geral');

  // Query para dados do dashboard
  const { data: statsData, isLoading: statsLoading } = useQuery({
    queryKey: ['relatorio-stats', dataInicio, dataFim, empresaSelecionada],
    queryFn: () => relatorioService.getStats({
      dataInicio,
      dataFim,
      empresaId: empresaSelecionada || undefined,
    }),
  });

  // Query para dados de classificação por período
  const { data: classificacaoData, isLoading: classificacaoLoading } = useQuery({
    queryKey: ['classificacao-periodo', dataInicio, dataFim, empresaSelecionada],
    queryFn: () => relatorioService.getClassificacaoPorPeriodo({
      dataInicio,
      dataFim,
      empresaId: empresaSelecionada || undefined,
    }),
  });

  // Query para lista de empresas
  const { data: empresas } = useQuery({
    queryKey: ['empresas-select'],
    queryFn: () => relatorioService.getEmpresas(),
  });

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

      enqueueSnackbar(`Relatório ${formato.toUpperCase()} exportado com sucesso`, { variant: 'success' });
    } catch (error) {
      enqueueSnackbar('Erro ao exportar relatório', { variant: 'error' });
    }
  };

  if (statsLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns} adapterLocale={ptBR}>
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        {/* Header */}
        <Box sx={{ mb: 4 }}>
          <Typography variant="h4" gutterBottom>
            Relatórios e Analytics
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Análises e relatórios sobre classificações NCM/CEST
          </Typography>
        </Box>

        {/* Filtros */}
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Filtros
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6} md={3}>
              <DatePicker
                label="Data Início"
                value={dataInicio}
                onChange={setDataInicio}
                renderInput={(params) => <TextField {...params} fullWidth />}
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <DatePicker
                label="Data Fim"
                value={dataFim}
                onChange={setDataFim}
                renderInput={(params) => <TextField {...params} fullWidth />}
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
                  <MenuItem value="">Todas</MenuItem>
                  {empresas?.map((empresa: any) => (
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
                  <MenuItem value="geral">Geral</MenuItem>
                  <MenuItem value="classificacao">Classificações</MenuItem>
                  <MenuItem value="conformidade">Conformidade</MenuItem>
                  <MenuItem value="produtividade">Produtividade</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </Paper>

        {/* Cards de Estatísticas */}
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Assessment sx={{ color: 'primary.main', mr: 1 }} />
                  <Typography variant="h6">
                    Total de Produtos
                  </Typography>
                </Box>
                <Typography variant="h4" color="primary">
                  {statsData?.totalProdutos?.toLocaleString() || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Produtos cadastrados
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <CheckCircle sx={{ color: 'success.main', mr: 1 }} />
                  <Typography variant="h6">
                    Classificados
                  </Typography>
                </Box>
                <Typography variant="h4" color="success.main">
                  {statsData?.totalClassificados?.toLocaleString() || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {statsData?.totalProdutos ? 
                    `${Math.round((statsData.totalClassificados / statsData.totalProdutos) * 100)}%` : 
                    '0%'
                  } do total
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Warning sx={{ color: 'warning.main', mr: 1 }} />
                  <Typography variant="h6">
                    Pendentes
                  </Typography>
                </Box>
                <Typography variant="h4" color="warning.main">
                  {statsData?.totalPendentes?.toLocaleString() || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Aguardando classificação
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Error sx={{ color: 'error.main', mr: 1 }} />
                  <Typography variant="h6">
                    Com Erro
                  </Typography>
                </Box>
                <Typography variant="h4" color="error.main">
                  {statsData?.totalErros?.toLocaleString() || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Requerem atenção
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Gráficos */}
        <Grid container spacing={3} sx={{ mb: 3 }}>
          {/* Gráfico de Pizza - Status */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Distribuição por Status
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
                  <Tooltip />
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
                    <Tooltip />
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
        <Paper sx={{ p: 3 }}>
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
      </Container>
    </LocalizationProvider>
  );
};

export default RelatoriosPage;
