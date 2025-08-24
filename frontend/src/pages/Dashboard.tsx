import React, { useState, useEffect } from 'react';
import {
  Container,
  Grid,
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  CardActions,
  Button,
  Alert,
  CircularProgress,
  Skeleton,
} from '@mui/material';
import {
  Business,
  Inventory,
  Assessment,
  PlayArrow,
  TrendingUp,
  CheckCircle,
  Warning,
} from '@mui/icons-material';
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
} from 'recharts';
import StatsCard from '../components/StatsCard';
import { useAuth } from '../hooks/useAuth';
import { api } from '../services/api'; // Importar a instância da API

interface DashboardStats {
  totalEmpresas: number;
  totalProdutos: number;
  produtosComNCM: number;
  produtosComCEST: number;
  classificacoesPendentes: number;
  accuracy: number;
}

const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
                const response = await api.get('/dashboard/stats');
        setStats(response.data);
        setError(null);
      } catch (err) {
        console.error("Erro ao buscar dados do dashboard:", err);
        setError("Não foi possível carregar os dados do dashboard. Usando dados de exemplo.");
        // Fallback para dados de exemplo em caso de erro
        // setStats({
        //   totalEmpresas: 12,
        //   totalProdutos: 8547,
        //   produtosComNCM: 7234,
        //   produtosComCEST: 3421,
        //   classificacoesPendentes: 156,
        //   accuracy: 94.2,
        // });
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  // Dados de exemplo para demonstração
  const monthlyData = [
    { month: 'Jan', classificacoes: 1200, accuracy: 92 },
    { month: 'Fev', classificacoes: 1350, accuracy: 93 },
    { month: 'Mar', classificacoes: 1180, accuracy: 94 },
    { month: 'Abr', classificacoes: 1420, accuracy: 95 },
    { month: 'Mai', classificacoes: 1650, accuracy: 94 },
    { month: 'Jun', classificacoes: 1580, accuracy: 96 },
  ];

  if (loading) {
    return (
      <Container maxWidth="xl">
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '80vh' }}>
          <CircularProgress />
          <Typography variant="h6" sx={{ ml: 2 }}>Carregando dados do dashboard...</Typography>
        </Box>
      </Container>
    );
  }

  if (!stats) {
    return (
      <Container maxWidth="xl">
        <Alert severity="error">
          {error || "Não foi possível carregar os dados do dashboard."}
        </Alert>
      </Container>
    );
  }

  const chartData = [
    { name: 'Com NCM', value: stats.produtosComNCM, color: '#4caf50' },
    { name: 'Sem NCM', value: stats.totalProdutos - stats.produtosComNCM, color: '#f44336' },
  ];

  return (
    <Container maxWidth="xl">
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom>
          Dashboard Executivo
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          Bem-vindo, {user?.full_name || user?.username}! Aqui está o resumo do sistema.
        </Typography>
        {error && <Alert severity="warning" sx={{ mt: 2 }}>{error}</Alert>}
      </Box>

      {/* Cards de Estatísticas */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatsCard
            title="Empresas Cadastradas"
            value={stats.totalEmpresas}
            icon={<Business />}
            status="info"
            trend={8.3}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatsCard
            title="Total de Produtos"
            value={stats.totalProdutos.toLocaleString()}
            icon={<Inventory />}
            status="success"
            trend={12.5}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatsCard
            title="Produtos com NCM"
            value={`${((stats.produtosComNCM / stats.totalProdutos) * 100).toFixed(1)}%`}
            subtitle={`${stats.produtosComNCM.toLocaleString()} de ${stats.totalProdutos.toLocaleString()}`}
            icon={<CheckCircle />}
            status="success"
            progress={(stats.produtosComNCM / stats.totalProdutos) * 100}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatsCard
            title="Accuracy Geral"
            value={`${stats.accuracy}%`}
            subtitle="Precisão das classificações"
            icon={<TrendingUp />}
            status="success"
            trend={2.1}
          />
        </Grid>
      </Grid>

      {/* Alertas e Ações Rápidas */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Classificações por Mês
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={monthlyData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="classificacoes" fill="#1976d2" />
              </BarChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3, mb: 2 }}>
            <Typography variant="h6" gutterBottom>
              Distribuição NCM
            </Typography>
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={chartData}
                  cx="50%"
                  cy="50%"
                  innerRadius={40}
                  outerRadius={80}
                  dataKey="value"
                >
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </Paper>

          {stats.classificacoesPendentes > 0 && (
            <Alert severity="warning" sx={{ mb: 2 }}>
              <Typography variant="body2">
                {stats.classificacoesPendentes} produtos precisam de revisão manual
              </Typography>
            </Alert>
          )}
        </Grid>
      </Grid>

      {/* Ações Rápidas */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Business sx={{ mr: 2 }} />
                <Typography variant="h6">Gerenciar Empresas</Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Cadastrar novas empresas e gerenciar informações existentes
              </Typography>
            </CardContent>
            <CardActions>
              <Button size="small" startIcon={<PlayArrow />}>
                Acessar
              </Button>
            </CardActions>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Inventory sx={{ mr: 2 }} />
                <Typography variant="h6">Classificar Produtos</Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Executar classificação automática de NCM/CEST
              </Typography>
            </CardContent>
            <CardActions>
              <Button size="small" startIcon={<PlayArrow />}>
                Executar
              </Button>
            </CardActions>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Assessment sx={{ mr: 2 }} />
                <Typography variant="h6">Relatórios</Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Gerar relatórios detalhados de auditoria e conformidade
              </Typography>
            </CardContent>
            <CardActions>
              <Button size="small" startIcon={<PlayArrow />}>
                Gerar
              </Button>
            </CardActions>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};

export default Dashboard;
