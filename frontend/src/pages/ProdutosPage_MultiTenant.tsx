import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
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
  Breadcrumbs,
  Link,
} from '@mui/material';
import {
  Add as AddIcon,
  Inventory as InventoryIcon,
  Psychology as PsychologyIcon,
  ArrowBack as ArrowBackIcon,
  Edit as EditIcon,
  Assessment as AssessmentIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

interface Produto {
  id: number;
  descricao: string;
  categoria: string;
  ncm_sugerido?: string;
  cest_sugerido?: string;
  confianca_ncm?: number;
  confianca_cest?: number;
  created_at: string;
}

interface Empresa {
  id: number;
  nome: string;
  cnpj: string;
}

const ProdutosPage: React.FC = () => {
  const { empresaId } = useParams<{ empresaId: string }>();
  const navigate = useNavigate();
  
  const [empresa, setEmpresa] = useState<Empresa | null>(null);
  const [produtos, setProdutos] = useState<Produto[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [open, setOpen] = useState(false);
  const [classifyOpen, setClassifyOpen] = useState(false);
  const [selectedProduto, setSelectedProduto] = useState<Produto | null>(null);
  const [formData, setFormData] = useState({
    descricao: '',
    categoria: '',
  });
  const [creating, setCreating] = useState(false);
  const [classifying, setClassifying] = useState(false);

  useEffect(() => {
    if (empresaId) {
      fetchEmpresaData();
      fetchProdutos();
    }
  }, [empresaId]);

  const fetchEmpresaData = async () => {
    try {
      const response = await axios.get('/empresas');
      const empresas = response.data || [];
      const empresaEncontrada = empresas.find((emp: Empresa) => emp.id === parseInt(empresaId!));
      setEmpresa(empresaEncontrada || null);
    } catch (err) {
      console.error('Error fetching empresa:', err);
    }
  };

  const fetchProdutos = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`/empresas/${empresaId}/produtos`);
      setProdutos(response.data?.produtos || []);
    } catch (err) {
      setError('Erro ao carregar produtos');
      console.error('Error fetching produtos:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    try {
      setCreating(true);
      const response = await axios.post(`/empresas/${empresaId}/produtos`, formData);
      
      if (response.data.success) {
        setOpen(false);
        setFormData({ descricao: '', categoria: '' });
        fetchProdutos();
      }
    } catch (err) {
      console.error('Error creating produto:', err);
      setError('Erro ao criar produto');
    } finally {
      setCreating(false);
    }
  };

  const handleClassify = async () => {
    if (!selectedProduto) return;
    
    try {
      setClassifying(true);
      const response = await axios.post(`/empresas/${empresaId}/classificar`, {
        descricao: selectedProduto.descricao,
        categoria: selectedProduto.categoria,
      });
      
      if (response.data.success) {
        setClassifyOpen(false);
        setSelectedProduto(null);
        fetchProdutos();
      }
    } catch (err) {
      console.error('Error classifying produto:', err);
      setError('Erro ao classificar produto');
    } finally {
      setClassifying(false);
    }
  };

  const getConfidenceColor = (confidence?: number) => {
    if (!confidence) return 'default';
    if (confidence >= 0.8) return 'success';
    if (confidence >= 0.6) return 'warning';
    return 'error';
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('pt-BR');
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      {/* Breadcrumbs */}
      <Breadcrumbs sx={{ mb: 2 }}>
        <Link 
          color="inherit" 
          href="#" 
          onClick={() => navigate('/empresas')}
          sx={{ display: 'flex', alignItems: 'center' }}
        >
          Empresas
        </Link>
        <Typography color="text.primary">
          {empresa?.nome || 'Produtos'}
        </Typography>
      </Breadcrumbs>

      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <IconButton onClick={() => navigate('/empresas')}>
            <ArrowBackIcon />
          </IconButton>
          <Box>
            <Typography variant="h4" gutterBottom sx={{ fontWeight: 600 }}>
              Produtos - {empresa?.nome}
            </Typography>
            <Typography variant="subtitle1" color="text.secondary">
              Banco dedicado: empresa_{empresa?.cnpj}
            </Typography>
          </Box>
        </Box>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setOpen(true)}
          size="large"
        >
          Novo Produto
        </Button>
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
                    Total Produtos
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 600 }}>
                    {produtos.length}
                  </Typography>
                </Box>
                <InventoryIcon color="primary" sx={{ fontSize: 40 }} />
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
                    Classificados
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 600 }}>
                    {produtos.filter(p => p.ncm_sugerido).length}
                  </Typography>
                </Box>
                <AssessmentIcon color="success" sx={{ fontSize: 40 }} />
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
                    {produtos.filter(p => !p.ncm_sugerido).length}
                  </Typography>
                </Box>
                <PsychologyIcon color="warning" sx={{ fontSize: 40 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom variant="overline">
                Taxa de Classificação
              </Typography>
              <Typography variant="h4" sx={{ fontWeight: 600 }}>
                {produtos.length > 0 ? Math.round((produtos.filter(p => p.ncm_sugerido).length / produtos.length) * 100) : 0}%
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tabela de Produtos */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Lista de Produtos
          </Typography>
          <TableContainer component={Paper} variant="outlined">
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell><strong>ID</strong></TableCell>
                  <TableCell><strong>Descrição</strong></TableCell>
                  <TableCell><strong>Categoria</strong></TableCell>
                  <TableCell><strong>NCM Sugerido</strong></TableCell>
                  <TableCell><strong>CEST Sugerido</strong></TableCell>
                  <TableCell><strong>Confiança</strong></TableCell>
                  <TableCell><strong>Criado em</strong></TableCell>
                  <TableCell><strong>Ações</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {produtos.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={8} align="center">
                      <Typography color="text.secondary">
                        Nenhum produto cadastrado
                      </Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  produtos.map((produto) => (
                    <TableRow key={produto.id} hover>
                      <TableCell>{produto.id}</TableCell>
                      <TableCell>
                        <Typography variant="body2" sx={{ maxWidth: 200 }}>
                          {produto.descricao}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip label={produto.categoria} size="small" variant="outlined" />
                      </TableCell>
                      <TableCell>
                        {produto.ncm_sugerido ? (
                          <Chip 
                            label={produto.ncm_sugerido} 
                            size="small" 
                            color="primary"
                            sx={{ fontFamily: 'monospace' }}
                          />
                        ) : (
                          <Typography variant="caption" color="text.secondary">
                            Não classificado
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell>
                        {produto.cest_sugerido ? (
                          <Chip 
                            label={produto.cest_sugerido} 
                            size="small" 
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
                        {produto.confianca_ncm ? (
                          <Chip 
                            label={`${Math.round(produto.confianca_ncm * 100)}%`}
                            size="small" 
                            color={getConfidenceColor(produto.confianca_ncm)}
                          />
                        ) : (
                          <Typography variant="caption" color="text.secondary">
                            -
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell>{formatDate(produto.created_at)}</TableCell>
                      <TableCell>
                        <IconButton
                          size="small"
                          onClick={() => {
                            setSelectedProduto(produto);
                            setClassifyOpen(true);
                          }}
                          title="Classificar com IA"
                          disabled={!!produto.ncm_sugerido}
                        >
                          <PsychologyIcon />
                        </IconButton>
                        <IconButton size="small" title="Editar">
                          <EditIcon />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* Dialog para Novo Produto */}
      <Dialog open={open} onClose={() => setOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Novo Produto</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <TextField
              fullWidth
              label="Descrição do Produto"
              value={formData.descricao}
              onChange={(e) => setFormData({ ...formData, descricao: e.target.value })}
              multiline
              rows={3}
              sx={{ mb: 2 }}
              placeholder="Ex: Smartphone Samsung Galaxy A54 128GB Preto"
            />
            <TextField
              fullWidth
              label="Categoria"
              value={formData.categoria}
              onChange={(e) => setFormData({ ...formData, categoria: e.target.value })}
              sx={{ mb: 2 }}
              placeholder="Ex: Eletrônicos, Medicamentos, Alimentos"
            />
            <Alert severity="info">
              Após criar o produto, use a função "Classificar com IA" para obter sugestões de NCM/CEST.
            </Alert>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>Cancelar</Button>
          <Button 
            onClick={handleCreate} 
            variant="contained"
            disabled={creating || !formData.descricao || !formData.categoria}
          >
            {creating ? <CircularProgress size={20} /> : 'Criar Produto'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Dialog para Classificação IA */}
      <Dialog open={classifyOpen} onClose={() => setClassifyOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Classificação com IA</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <Typography variant="subtitle1" gutterBottom>
              <strong>Produto:</strong> {selectedProduto?.descricao}
            </Typography>
            <Typography variant="subtitle2" gutterBottom>
              <strong>Categoria:</strong> {selectedProduto?.categoria}
            </Typography>
            <Alert severity="info" sx={{ mt: 2 }}>
              O sistema irá analisar a descrição e categoria do produto para sugerir os códigos NCM e CEST mais apropriados.
            </Alert>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setClassifyOpen(false)}>Cancelar</Button>
          <Button 
            onClick={handleClassify} 
            variant="contained"
            disabled={classifying}
            startIcon={<PsychologyIcon />}
          >
            {classifying ? <CircularProgress size={20} /> : 'Classificar com IA'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ProdutosPage;
