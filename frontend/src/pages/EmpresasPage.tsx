import React, { useState, useEffect } from 'react';
import {
  Box, Paper, Typography, Button, Table, TableBody,
  TableCell, TableContainer, TableHead, TableRow,
  IconButton, Chip, TextField, InputAdornment,
  Menu, MenuItem, Dialog, DialogTitle, DialogContent,
  DialogActions, Card, CardContent, Grid, Alert,
  Tabs, Tab, Divider
} from '@mui/material';
import {
  Add, Search, MoreVert, Edit, Delete, Visibility,
  Business, LocationOn, Phone, Email, Settings,
  Archive, Restore, Download
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

interface Empresa {
  id: string;
  razaoSocial: string;
  nomeFantasia: string;
  cnpj: string;
  email: string;
  telefone: string;
  cidade: string;
  estado: string;
  status: 'ATIVA' | 'INATIVA' | 'SUSPENSA';
  dataCadastro: string;
  ultimoAcesso: string;
  totalProdutos: number;
  regimeTributario: string;
  contribuinteICMS: boolean;
}

const EmpresasPage: React.FC = () => {
  const navigate = useNavigate();
  const [empresas, setEmpresas] = useState<Empresa[]>([]);
  const [filtro, setFiltro] = useState('');
  const [tabValue, setTabValue] = useState(0);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [empresaSelecionada, setEmpresaSelecionada] = useState<Empresa | null>(null);
  const [dialogDetalhes, setDialogDetalhes] = useState(false);
  const [dialogExcluir, setDialogExcluir] = useState(false);
  const [carregando, setCarregando] = useState(true);

  useEffect(() => {
    carregarEmpresas();
  }, []);

  const carregarEmpresas = async () => {
    setCarregando(true);
    try {
      const response = await fetch('/api/tenants');
      if (response.ok) {
        const data = await response.json();
        
        // Simular dados se API não retornar dados completos
        const empresasDemo: Empresa[] = [
          {
            id: '1',
            razaoSocial: 'ABC Comércio de Produtos Ltda',
            nomeFantasia: 'ABC Loja',
            cnpj: '12.345.678/0001-90',
            email: 'contato@abcloja.com.br',
            telefone: '(11) 99999-9999',
            cidade: 'São Paulo',
            estado: 'SP',
            status: 'ATIVA',
            dataCadastro: '2025-01-15',
            ultimoAcesso: '2025-08-23',
            totalProdutos: 1250,
            regimeTributario: 'SIMPLES_NACIONAL',
            contribuinteICMS: true
          },
          {
            id: '2',
            razaoSocial: 'XYZ Indústria e Comércio S.A.',
            nomeFantasia: 'XYZ Industrial',
            cnpj: '98.765.432/0001-10',
            email: 'admin@xyzindustrial.com',
            telefone: '(21) 88888-8888',
            cidade: 'Rio de Janeiro',
            estado: 'RJ',
            status: 'ATIVA',
            dataCadastro: '2024-11-20',
            ultimoAcesso: '2025-08-22',
            totalProdutos: 850,
            regimeTributario: 'LUCRO_PRESUMIDO',
            contribuinteICMS: true
          },
          {
            id: '3',
            razaoSocial: 'Tech Solutions Informática ME',
            nomeFantasia: 'Tech Solutions',
            cnpj: '45.678.901/0001-23',
            email: 'contato@techsolutions.com.br',
            telefone: '(31) 77777-7777',
            cidade: 'Belo Horizonte',
            estado: 'MG',
            status: 'INATIVA',
            dataCadastro: '2024-08-10',
            ultimoAcesso: '2025-06-15',
            totalProdutos: 320,
            regimeTributario: 'SIMPLES_NACIONAL',
            contribuinteICMS: false
          }
        ];
        
        setEmpresas(data.length > 0 ? data : empresasDemo);
      }
    } catch (error) {
      console.error('Erro ao carregar empresas:', error);
    } finally {
      setCarregando(false);
    }
  };

  const handleMenuClick = (event: React.MouseEvent<HTMLElement>, empresa: Empresa) => {
    setAnchorEl(event.currentTarget);
    setEmpresaSelecionada(empresa);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setEmpresaSelecionada(null);
  };

  const abrirDetalhes = () => {
    setDialogDetalhes(true);
    handleMenuClose();
  };

  const editarEmpresa = () => {
    if (empresaSelecionada) {
      navigate(`/empresas/editar/${empresaSelecionada.id}`);
    }
    handleMenuClose();
  };

  const confirmarExclusao = () => {
    setDialogExcluir(true);
    handleMenuClose();
  };

  const excluirEmpresa = async () => {
    if (empresaSelecionada) {
      try {
        const response = await fetch(`/api/tenants/${empresaSelecionada.id}`, {
          method: 'DELETE'
        });
        
        if (response.ok) {
          setEmpresas(prev => prev.filter(emp => emp.id !== empresaSelecionada.id));
          alert('Empresa excluída com sucesso!');
        }
      } catch (error) {
        console.error('Erro ao excluir empresa:', error);
        alert('Erro ao excluir empresa.');
      }
    }
    setDialogExcluir(false);
    setEmpresaSelecionada(null);
  };

  const alterarStatus = async (novoStatus: string) => {
    if (empresaSelecionada) {
      try {
        const response = await fetch(`/api/tenants/${empresaSelecionada.id}/status`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ status: novoStatus })
        });
        
        if (response.ok) {
          setEmpresas(prev =>
            prev.map(emp =>
              emp.id === empresaSelecionada.id
                ? { ...emp, status: novoStatus as any }
                : emp
            )
          );
          alert(`Status alterado para ${novoStatus}!`);
        }
      } catch (error) {
        console.error('Erro ao alterar status:', error);
      }
    }
    handleMenuClose();
  };

  const empresasFiltradas = empresas.filter(empresa => {
    const termo = filtro.toLowerCase();
    return (
      empresa.razaoSocial.toLowerCase().includes(termo) ||
      empresa.nomeFantasia.toLowerCase().includes(termo) ||
      empresa.cnpj.includes(termo) ||
      empresa.email.toLowerCase().includes(termo)
    );
  });

  const empresasPorStatus = {
    todas: empresasFiltradas,
    ativas: empresasFiltradas.filter(emp => emp.status === 'ATIVA'),
    inativas: empresasFiltradas.filter(emp => emp.status === 'INATIVA'),
    suspensas: empresasFiltradas.filter(emp => emp.status === 'SUSPENSA')
  };

  const getEmpresasExibidas = () => {
    switch (tabValue) {
      case 1: return empresasPorStatus.ativas;
      case 2: return empresasPorStatus.inativas;
      case 3: return empresasPorStatus.suspensas;
      default: return empresasPorStatus.todas;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ATIVA': return 'success';
      case 'INATIVA': return 'default';
      case 'SUSPENSA': return 'warning';
      default: return 'default';
    }
  };

  return (
    <Box sx={{ maxWidth: 1400, mx: 'auto', p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">
          Gerenciar Empresas
        </Typography>
        
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={() => navigate('/empresas/cadastrar')}
          size="large"
        >
          Nova Empresa
        </Button>
      </Box>

      {/* Estatísticas rápidas */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total de Empresas
              </Typography>
              <Typography variant="h4">
                {empresas.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Empresas Ativas
              </Typography>
              <Typography variant="h4" color="success.main">
                {empresasPorStatus.ativas.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total de Produtos
              </Typography>
              <Typography variant="h4">
                {empresas.reduce((total, emp) => total + emp.totalProdutos, 0).toLocaleString()}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Novos Este Mês
              </Typography>
              <Typography variant="h4" color="primary.main">
                2
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Paper sx={{ p: 3 }}>
        {/* Filtros */}
        <Box sx={{ mb: 3 }}>
          <TextField
            fullWidth
            placeholder="Buscar por razão social, CNPJ, email..."
            value={filtro}
            onChange={(e) => setFiltro(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <Search />
                </InputAdornment>
              ),
            }}
            sx={{ maxWidth: 400 }}
          />
        </Box>

        {/* Tabs por status */}
        <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)} sx={{ mb: 3 }}>
          <Tab label={`Todas (${empresasPorStatus.todas.length})`} />
          <Tab label={`Ativas (${empresasPorStatus.ativas.length})`} />
          <Tab label={`Inativas (${empresasPorStatus.inativas.length})`} />
          <Tab label={`Suspensas (${empresasPorStatus.suspensas.length})`} />
        </Tabs>

        {/* Tabela */}
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Empresa</TableCell>
                <TableCell>CNPJ</TableCell>
                <TableCell>Contato</TableCell>
                <TableCell>Localização</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Produtos</TableCell>
                <TableCell>Último Acesso</TableCell>
                <TableCell>Ações</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {getEmpresasExibidas().map((empresa) => (
                <TableRow key={empresa.id} hover>
                  <TableCell>
                    <Box>
                      <Typography variant="subtitle2">
                        {empresa.razaoSocial}
                      </Typography>
                      {empresa.nomeFantasia && (
                        <Typography variant="body2" color="textSecondary">
                          {empresa.nomeFantasia}
                        </Typography>
                      )}
                    </Box>
                  </TableCell>
                  <TableCell>{empresa.cnpj}</TableCell>
                  <TableCell>
                    <Box>
                      <Typography variant="body2">{empresa.email}</Typography>
                      <Typography variant="body2" color="textSecondary">
                        {empresa.telefone}
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell>
                    {empresa.cidade}/{empresa.estado}
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={empresa.status}
                      color={getStatusColor(empresa.status) as any}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>{empresa.totalProdutos.toLocaleString()}</TableCell>
                  <TableCell>
                    {new Date(empresa.ultimoAcesso).toLocaleDateString('pt-BR')}
                  </TableCell>
                  <TableCell>
                    <IconButton
                      onClick={(e) => handleMenuClick(e, empresa)}
                      size="small"
                    >
                      <MoreVert />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>

        {getEmpresasExibidas().length === 0 && (
          <Alert severity="info" sx={{ mt: 2 }}>
            Nenhuma empresa encontrada com os critérios de busca.
          </Alert>
        )}
      </Paper>

      {/* Menu de ações */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={abrirDetalhes}>
          <Visibility sx={{ mr: 1 }} />
          Ver Detalhes
        </MenuItem>
        <MenuItem onClick={editarEmpresa}>
          <Edit sx={{ mr: 1 }} />
          Editar
        </MenuItem>
        <Divider />
        {empresaSelecionada?.status === 'ATIVA' ? (
          <MenuItem onClick={() => alterarStatus('INATIVA')}>
            <Archive sx={{ mr: 1 }} />
            Desativar
          </MenuItem>
        ) : (
          <MenuItem onClick={() => alterarStatus('ATIVA')}>
            <Restore sx={{ mr: 1 }} />
            Ativar
          </MenuItem>
        )}
        <MenuItem onClick={() => alterarStatus('SUSPENSA')}>
          <Settings sx={{ mr: 1 }} />
          Suspender
        </MenuItem>
        <Divider />
        <MenuItem onClick={confirmarExclusao} sx={{ color: 'error.main' }}>
          <Delete sx={{ mr: 1 }} />
          Excluir
        </MenuItem>
      </Menu>

      {/* Dialog de detalhes */}
      <Dialog open={dialogDetalhes} onClose={() => setDialogDetalhes(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          Detalhes da Empresa
        </DialogTitle>
        <DialogContent>
          {empresaSelecionada && (
            <Grid container spacing={3} sx={{ mt: 1 }}>
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      <Business sx={{ mr: 1, verticalAlign: 'middle' }} />
                      Dados Básicos
                    </Typography>
                    <Typography variant="body2">
                      <strong>Razão Social:</strong> {empresaSelecionada.razaoSocial}
                    </Typography>
                    <Typography variant="body2">
                      <strong>Nome Fantasia:</strong> {empresaSelecionada.nomeFantasia}
                    </Typography>
                    <Typography variant="body2">
                      <strong>CNPJ:</strong> {empresaSelecionada.cnpj}
                    </Typography>
                    <Typography variant="body2">
                      <strong>Status:</strong> {empresaSelecionada.status}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      <Email sx={{ mr: 1, verticalAlign: 'middle' }} />
                      Contato
                    </Typography>
                    <Typography variant="body2">
                      <strong>E-mail:</strong> {empresaSelecionada.email}
                    </Typography>
                    <Typography variant="body2">
                      <strong>Telefone:</strong> {empresaSelecionada.telefone}
                    </Typography>
                    <Typography variant="body2">
                      <strong>Localização:</strong> {empresaSelecionada.cidade}/{empresaSelecionada.estado}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Informações Fiscais
                    </Typography>
                    <Typography variant="body2">
                      <strong>Regime Tributário:</strong> {empresaSelecionada.regimeTributario}
                    </Typography>
                    <Typography variant="body2">
                      <strong>Contribuinte ICMS:</strong> {empresaSelecionada.contribuinteICMS ? 'Sim' : 'Não'}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Estatísticas
                    </Typography>
                    <Typography variant="body2">
                      <strong>Data de Cadastro:</strong> {new Date(empresaSelecionada.dataCadastro).toLocaleDateString('pt-BR')}
                    </Typography>
                    <Typography variant="body2">
                      <strong>Último Acesso:</strong> {new Date(empresaSelecionada.ultimoAcesso).toLocaleDateString('pt-BR')}
                    </Typography>
                    <Typography variant="body2">
                      <strong>Total de Produtos:</strong> {empresaSelecionada.totalProdutos.toLocaleString()}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogDetalhes(false)}>
            Fechar
          </Button>
          <Button variant="contained" onClick={editarEmpresa}>
            Editar
          </Button>
        </DialogActions>
      </Dialog>

      {/* Dialog de confirmação de exclusão */}
      <Dialog open={dialogExcluir} onClose={() => setDialogExcluir(false)}>
        <DialogTitle>Confirmar Exclusão</DialogTitle>
        <DialogContent>
          <Typography>
            Tem certeza que deseja excluir a empresa <strong>{empresaSelecionada?.razaoSocial}</strong>?
          </Typography>
          <Alert severity="warning" sx={{ mt: 2 }}>
            Esta ação não pode ser desfeita. Todos os dados da empresa serão perdidos.
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogExcluir(false)}>
            Cancelar
          </Button>
          <Button variant="contained" color="error" onClick={excluirEmpresa}>
            Excluir
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default EmpresasPage;
