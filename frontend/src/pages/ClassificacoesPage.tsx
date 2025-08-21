import React, { useEffect, useState } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Alert,
  CircularProgress,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Tabs,
  Tab,
} from '@mui/material';
import {
  Psychology as PsychologyIcon,
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
  Edit as EditIcon,
  Visibility as VisibilityIcon,
  Assessment as AssessmentIcon,
  TrendingUp as TrendingUpIcon,
  Warning as WarningIcon,
} from '@mui/icons-material';
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';
import axios from 'axios';

interface Classificacao {
  id: number;
  empresa_id: number;
  empresa_nome: string;
  produto_id: number;
  produto_descricao: string;
  categoria: string;
  ncm_sugerido: string;
  cest_sugerido?: string;
  confianca_ncm: number;
  confianca_cest?: number;
  status: 'pendente' | 'aprovado' | 'rejeitado';
  justificativa: string;
  created_at: string;
  reviewed_at?: string;
  reviewed_by?: string;
}

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
      {...other}
    >
      {value === index && <Box>{children}</Box>}
    </div>
  );
}

const ClassificacoesPage: React.FC = () => {
  const [classificacoes, setClassificacoes] = useState<Classificacao[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedClassificacao, setSelectedClassificacao] = useState<Classificacao | null>(null);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [tabValue, setTabValue] = useState(0);
  const [statusFilter, setStatusFilter] = useState<string>('all');

  useEffect(() => {
    fetchClassificacoes();
  }, []);

  const fetchClassificacoes = async () => {
    try {
      setLoading(true);
      // Simular dados já que não temos endpoint específico ainda
      const mockData: Classificacao[] = [
        {
          id: 1,
          empresa_id: 1,
          empresa_nome: 'ABC Farmácia Ltda',
          produto_id: 1,
          produto_descricao: 'Paracetamol 500mg comprimidos',
          categoria: 'Medicamentos',
          ncm_sugerido: '3004.20.90',
          cest_sugerido: '20.001.00',
          confianca_ncm: 0.95,
          confianca_cest: 0.92,
          status: 'aprovado',
          justificativa: 'Medicamento de venda livre, classificação adequada para analgésicos',
          created_at: '2025-08-20T10:00:00Z',
          reviewed_at: '2025-08-20T10:30:00Z',
          reviewed_by: 'Auditor Fiscal'
        },
        {
          id: 2,
          empresa_id: 2,
          empresa_nome: 'Tech Solutions Informática',
          produto_id: 2,
          produto_descricao: 'Smartphone Samsung Galaxy A54 128GB',
          categoria: 'Eletrônicos',
          ncm_sugerido: '8517.12.00',
          confianca_ncm: 0.88,
          status: 'pendente',
          justificativa: 'Aparelho de telefonia celular com acesso à internet',
          created_at: '2025-08-20T11:00:00Z',
        },
        {
          id: 3,
          empresa_id: 3,
          empresa_nome: 'SuperMercado Central Ltda',
          produto_id: 3,
          produto_descricao: 'Leite UHT integral 1L',
          categoria: 'Alimentos',
          ncm_sugerido: '0401.10.10',
          confianca_ncm: 0.75,
          status: 'rejeitado',
          justificativa: 'Classificação incorreta - produto processado',
          created_at: '2025-08-20T09:00:00Z',
          reviewed_at: '2025-08-20T14:00:00Z',
          reviewed_by: 'Especialista NCM'
        }
      ];
      setClassificacoes(mockData);
    } catch (err) {
      setError('Erro ao carregar classificações');
      console.error('Error fetching classificações:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (id: number) => {
    try {
      // Simular aprovação
      setClassificacoes(prev => 
        prev.map(c => 
          c.id === id 
            ? { ...c, status: 'aprovado' as const, reviewed_at: new Date().toISOString(), reviewed_by: 'Sistema' }
            : c
        )
      );
    } catch (err) {
      setError('Erro ao aprovar classificação');
    }
  };

  const handleReject = async (id: number) => {
    try {
      // Simular rejeição
      setClassificacoes(prev => 
        prev.map(c => 
          c.id === id 
            ? { ...c, status: 'rejeitado' as const, reviewed_at: new Date().toISOString(), reviewed_by: 'Sistema' }
            : c
        )
      );
    } catch (err) {
      setError('Erro ao rejeitar classificação');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'aprovado': return 'success';
      case 'rejeitado': return 'error';
      case 'pendente': return 'warning';
      default: return 'default';
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'success';
    if (confidence >= 0.6) return 'warning';
    return 'error';
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const filteredClassificacoes = statusFilter === 'all' 
    ? classificacoes 
    : classificacoes.filter(c => c.status === statusFilter);

  // Dados para gráficos
  const statusData = [
    { name: 'Aprovadas', value: classificacoes.filter(c => c.status === 'aprovado').length, color: '#4caf50' },
    { name: 'Pendentes', value: classificacoes.filter(c => c.status === 'pendente').length, color: '#ff9800' },
    { name: 'Rejeitadas', value: classificacoes.filter(c => c.status === 'rejeitado').length, color: '#f44336' },
  ];

  const empresaData = classificacoes.reduce((acc, c) => {
    const existing = acc.find(item => item.empresa === c.empresa_nome);
    if (existing) {
      existing.total += 1;
    } else {
      acc.push({ empresa: c.empresa_nome.substring(0, 15), total: 1 });
    }
    return acc;
  }, [] as Array<{ empresa: string; total: number }>);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" gutterBottom sx={{ fontWeight: 600 }}>
          Classificações IA
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          Gerenciamento e aprovação de classificações automáticas NCM/CEST
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Statistics Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="text.secondary" gutterBottom variant="overline">
                    Total Classificações
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 600 }}>
                    {classificacoes.length}
                  </Typography>
                </Box>
                <AssessmentIcon color="primary" sx={{ fontSize: 40 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="text.secondary" gutterBottom variant="overline">
                    Aprovadas
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 600 }}>
                    {classificacoes.filter(c => c.status === 'aprovado').length}
                  </Typography>
                </Box>
                <CheckCircleIcon color="success" sx={{ fontSize: 40 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="text.secondary" gutterBottom variant="overline">
                    Pendentes
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 600 }}>
                    {classificacoes.filter(c => c.status === 'pendente').length}
                  </Typography>
                </Box>
                <WarningIcon color="warning" sx={{ fontSize: 40 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="text.secondary" gutterBottom variant="overline">
                    Taxa de Aprovação
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 600 }}>
                    {classificacoes.length > 0 
                      ? Math.round((classificacoes.filter(c => c.status === 'aprovado').length / classificacoes.length) * 100)
                      : 0}%
                  </Typography>
                </Box>
                <TrendingUpIcon color="success" sx={{ fontSize: 40 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Gráficos */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Status das Classificações
              </Typography>
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie
                    data={statusData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {statusData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
              <Box sx={{ mt: 2 }}>
                {statusData.map((entry) => (
                  <Box key={entry.name} sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <Box
                      sx={{
                        width: 12,
                        height: 12,
                        backgroundColor: entry.color,
                        borderRadius: '50%',
                        mr: 1,
                      }}
                    />
                    <Typography variant="body2">
                      {entry.name}: {entry.value}
                    </Typography>
                  </Box>
                ))}
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Classificações por Empresa
              </Typography>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={empresaData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="empresa" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="total" fill="#1976d2" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Filtros e Tabela */}
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">
              Lista de Classificações
            </Typography>
            <FormControl size="small" sx={{ minWidth: 150 }}>
              <InputLabel>Filtrar por Status</InputLabel>
              <Select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                label="Filtrar por Status"
              >
                <MenuItem value="all">Todos</MenuItem>
                <MenuItem value="pendente">Pendentes</MenuItem>
                <MenuItem value="aprovado">Aprovadas</MenuItem>
                <MenuItem value="rejeitado">Rejeitadas</MenuItem>
              </Select>
            </FormControl>
          </Box>

          <TableContainer component={Paper} variant="outlined">
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell><strong>ID</strong></TableCell>
                  <TableCell><strong>Empresa</strong></TableCell>
                  <TableCell><strong>Produto</strong></TableCell>
                  <TableCell><strong>NCM Sugerido</strong></TableCell>
                  <TableCell><strong>CEST</strong></TableCell>
                  <TableCell><strong>Confiança</strong></TableCell>
                  <TableCell><strong>Status</strong></TableCell>
                  <TableCell><strong>Data</strong></TableCell>
                  <TableCell><strong>Ações</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredClassificacoes.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={9} align="center">
                      <Typography color="text.secondary">
                        Nenhuma classificação encontrada
                      </Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredClassificacoes.map((classificacao) => (
                    <TableRow key={classificacao.id} hover>
                      <TableCell>{classificacao.id}</TableCell>
                      <TableCell>
                        <Typography variant="body2" sx={{ fontWeight: 500 }}>
                          {classificacao.empresa_nome}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" sx={{ maxWidth: 200 }}>
                          {classificacao.produto_descricao}
                        </Typography>
                        <Chip 
                          label={classificacao.categoria} 
                          size="small" 
                          variant="outlined"
                          sx={{ mt: 0.5 }}
                        />
                      </TableCell>
                      <TableCell>
                        <Chip 
                          label={classificacao.ncm_sugerido}
                          color="primary" 
                          sx={{ fontFamily: 'monospace' }}
                        />
                      </TableCell>
                      <TableCell>
                        {classificacao.cest_sugerido ? (
                          <Chip 
                            label={classificacao.cest_sugerido}
                            color="secondary" 
                            sx={{ fontFamily: 'monospace' }}
                          />
                        ) : (
                          <Typography variant="caption" color="text.secondary">
                            N/A
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell>
                        <Chip 
                          label={`${Math.round(classificacao.confianca_ncm * 100)}%`}
                          size="small" 
                          color={getConfidenceColor(classificacao.confianca_ncm)}
                        />
                      </TableCell>
                      <TableCell>
                        <Chip 
                          label={classificacao.status}
                          color={getStatusColor(classificacao.status)}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="caption">
                          {formatDate(classificacao.created_at)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <IconButton
                          size="small"
                          onClick={() => {
                            setSelectedClassificacao(classificacao);
                            setDetailsOpen(true);
                          }}
                          title="Ver Detalhes"
                        >
                          <VisibilityIcon />
                        </IconButton>
                        {classificacao.status === 'pendente' && (
                          <>
                            <IconButton
                              size="small"
                              onClick={() => handleApprove(classificacao.id)}
                              title="Aprovar"
                              color="success"
                            >
                              <CheckCircleIcon />
                            </IconButton>
                            <IconButton
                              size="small"
                              onClick={() => handleReject(classificacao.id)}
                              title="Rejeitar"
                              color="error"
                            >
                              <CancelIcon />
                            </IconButton>
                          </>
                        )}
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* Dialog de Detalhes */}
      <Dialog open={detailsOpen} onClose={() => setDetailsOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          Detalhes da Classificação #{selectedClassificacao?.id}
        </DialogTitle>
        <DialogContent>
          {selectedClassificacao && (
            <Box sx={{ pt: 2 }}>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" gutterBottom>Empresa</Typography>
                  <Typography variant="body2" sx={{ mb: 2 }}>
                    {selectedClassificacao.empresa_nome}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" gutterBottom>Status</Typography>
                  <Chip 
                    label={selectedClassificacao.status}
                    color={getStatusColor(selectedClassificacao.status)}
                    sx={{ mb: 2 }}
                  />
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="subtitle2" gutterBottom>Descrição do Produto</Typography>
                  <Typography variant="body2" sx={{ mb: 2 }}>
                    {selectedClassificacao.produto_descricao}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" gutterBottom>NCM Sugerido</Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                    <Chip 
                      label={selectedClassificacao.ncm_sugerido}
                      color="primary"
                      sx={{ fontFamily: 'monospace' }}
                    />
                    <Chip 
                      label={`${Math.round(selectedClassificacao.confianca_ncm * 100)}%`}
                      size="small" 
                      color={getConfidenceColor(selectedClassificacao.confianca_ncm)}
                    />
                  </Box>
                </Grid>
                {selectedClassificacao.cest_sugerido && (
                  <Grid item xs={12} sm={6}>
                    <Typography variant="subtitle2" gutterBottom>CEST Sugerido</Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                      <Chip 
                        label={selectedClassificacao.cest_sugerido}
                        color="secondary"
                        sx={{ fontFamily: 'monospace' }}
                      />
                      {selectedClassificacao.confianca_cest && (
                        <Chip 
                          label={`${Math.round(selectedClassificacao.confianca_cest * 100)}%`}
                          size="small" 
                          color={getConfidenceColor(selectedClassificacao.confianca_cest)}
                        />
                      )}
                    </Box>
                  </Grid>
                )}
                <Grid item xs={12}>
                  <Typography variant="subtitle2" gutterBottom>Justificativa</Typography>
                  <Typography variant="body2" sx={{ mb: 2 }}>
                    {selectedClassificacao.justificativa}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" gutterBottom>Criado em</Typography>
                  <Typography variant="body2">
                    {formatDate(selectedClassificacao.created_at)}
                  </Typography>
                </Grid>
                {selectedClassificacao.reviewed_at && (
                  <Grid item xs={12} sm={6}>
                    <Typography variant="subtitle2" gutterBottom>Revisado em</Typography>
                    <Typography variant="body2">
                      {formatDate(selectedClassificacao.reviewed_at)}
                    </Typography>
                    {selectedClassificacao.reviewed_by && (
                      <Typography variant="caption" display="block">
                        por {selectedClassificacao.reviewed_by}
                      </Typography>
                    )}
                  </Grid>
                )}
              </Grid>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailsOpen(false)}>Fechar</Button>
          {selectedClassificacao?.status === 'pendente' && (
            <>
              <Button 
                onClick={() => {
                  handleApprove(selectedClassificacao.id);
                  setDetailsOpen(false);
                }}
                color="success"
                variant="contained"
              >
                Aprovar
              </Button>
              <Button 
                onClick={() => {
                  handleReject(selectedClassificacao.id);
                  setDetailsOpen(false);
                }}
                color="error"
                variant="outlined"
              >
                Rejeitar
              </Button>
            </>
          )}
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ClassificacoesPage;
