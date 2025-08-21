import React, { useEffect, useState } from 'react';
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
  Tabs,
  Tab,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
} from '@mui/material';
import {
  Add as AddIcon,
  Star as StarIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Verified as VerifiedIcon,
  School as SchoolIcon,
} from '@mui/icons-material';
import axios from 'axios';

interface GoldenSetItem {
  id: number;
  tipo: 'ncm' | 'cest';
  codigo: string;
  descricao: string;
  categoria: string;
  validado_por: string;
  confianca: number;
  created_at: string;
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
      id={`golden-set-tabpanel-${index}`}
      aria-labelledby={`golden-set-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const GoldenSetPage: React.FC = () => {
  const [goldenSetItems, setGoldenSetItems] = useState<GoldenSetItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [open, setOpen] = useState(false);
  const [tabValue, setTabValue] = useState(0);
  const [formData, setFormData] = useState({
    tipo: 'ncm' as 'ncm' | 'cest',
    codigo: '',
    descricao: '',
    categoria: '',
    validado_por: 'Sistema',
    confianca: 1.0,
  });
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    fetchGoldenSet();
  }, []);

  const fetchGoldenSet = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/golden-set/ncm');
      setGoldenSetItems(response.data?.items || []);
    } catch (err) {
      setError('Erro ao carregar Golden Set');
      console.error('Error fetching golden set:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    try {
      setCreating(true);
      const response = await axios.post('/golden-set/ncm', formData);
      
      if (response.data.success) {
        setOpen(false);
        setFormData({
          tipo: 'ncm',
          codigo: '',
          descricao: '',
          categoria: '',
          validado_por: 'Sistema',
          confianca: 1.0,
        });
        fetchGoldenSet();
      }
    } catch (err) {
      console.error('Error creating golden set item:', err);
      setError('Erro ao criar item do Golden Set');
    } finally {
      setCreating(false);
    }
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('pt-BR');
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.9) return 'success';
    if (confidence >= 0.7) return 'warning';
    return 'error';
  };

  const ncmItems = goldenSetItems.filter(item => item.tipo === 'ncm');
  const cestItems = goldenSetItems.filter(item => item.tipo === 'cest');

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
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" gutterBottom sx={{ fontWeight: 600 }}>
            Golden Set - Base de Conhecimento
          </Typography>
          <Typography variant="subtitle1" color="text.secondary">
            Classificações validadas manualmente para treinamento e referência
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setOpen(true)}
          size="large"
        >
          Novo Item
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
                    Total Itens
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 600 }}>
                    {goldenSetItems.length}
                  </Typography>
                </Box>
                <StarIcon color="warning" sx={{ fontSize: 40 }} />
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
                    Códigos NCM
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 600 }}>
                    {ncmItems.length}
                  </Typography>
                </Box>
                <VerifiedIcon color="primary" sx={{ fontSize: 40 }} />
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
                    Códigos CEST
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 600 }}>
                    {cestItems.length}
                  </Typography>
                </Box>
                <SchoolIcon color="secondary" sx={{ fontSize: 40 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom variant="overline">
                Qualidade Média
              </Typography>
              <Typography variant="h4" sx={{ fontWeight: 600 }}>
                {goldenSetItems.length > 0 
                  ? Math.round((goldenSetItems.reduce((sum, item) => sum + item.confianca, 0) / goldenSetItems.length) * 100)
                  : 0}%
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tabs para NCM e CEST */}
      <Card>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={handleTabChange}>
            <Tab 
              label={`NCM (${ncmItems.length})`} 
              icon={<VerifiedIcon />}
              iconPosition="start"
            />
            <Tab 
              label={`CEST (${cestItems.length})`} 
              icon={<SchoolIcon />}
              iconPosition="start"
            />
          </Tabs>
        </Box>

        <TabPanel value={tabValue} index={0}>
          <Typography variant="h6" gutterBottom>
            Códigos NCM Validados
          </Typography>
          <TableContainer component={Paper} variant="outlined">
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell><strong>Código NCM</strong></TableCell>
                  <TableCell><strong>Descrição</strong></TableCell>
                  <TableCell><strong>Categoria</strong></TableCell>
                  <TableCell><strong>Validado por</strong></TableCell>
                  <TableCell><strong>Confiança</strong></TableCell>
                  <TableCell><strong>Criado em</strong></TableCell>
                  <TableCell><strong>Ações</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {ncmItems.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} align="center">
                      <Typography color="text.secondary">
                        Nenhum código NCM no Golden Set
                      </Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  ncmItems.map((item) => (
                    <TableRow key={item.id} hover>
                      <TableCell>
                        <Chip 
                          label={item.codigo}
                          color="primary" 
                          sx={{ fontFamily: 'monospace', fontWeight: 600 }}
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" sx={{ maxWidth: 300 }}>
                          {item.descricao}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip label={item.categoria} size="small" variant="outlined" />
                      </TableCell>
                      <TableCell>{item.validado_por}</TableCell>
                      <TableCell>
                        <Chip 
                          label={`${Math.round(item.confianca * 100)}%`}
                          size="small" 
                          color={getConfidenceColor(item.confianca)}
                        />
                      </TableCell>
                      <TableCell>{formatDate(item.created_at)}</TableCell>
                      <TableCell>
                        <IconButton size="small" title="Editar">
                          <EditIcon />
                        </IconButton>
                        <IconButton size="small" title="Excluir" color="error">
                          <DeleteIcon />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <Typography variant="h6" gutterBottom>
            Códigos CEST Validados
          </Typography>
          <TableContainer component={Paper} variant="outlined">
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell><strong>Código CEST</strong></TableCell>
                  <TableCell><strong>Descrição</strong></TableCell>
                  <TableCell><strong>Categoria</strong></TableCell>
                  <TableCell><strong>Validado por</strong></TableCell>
                  <TableCell><strong>Confiança</strong></TableCell>
                  <TableCell><strong>Criado em</strong></TableCell>
                  <TableCell><strong>Ações</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {cestItems.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} align="center">
                      <Typography color="text.secondary">
                        Nenhum código CEST no Golden Set
                      </Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  cestItems.map((item) => (
                    <TableRow key={item.id} hover>
                      <TableCell>
                        <Chip 
                          label={item.codigo}
                          color="secondary" 
                          sx={{ fontFamily: 'monospace', fontWeight: 600 }}
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" sx={{ maxWidth: 300 }}>
                          {item.descricao}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip label={item.categoria} size="small" variant="outlined" />
                      </TableCell>
                      <TableCell>{item.validado_por}</TableCell>
                      <TableCell>
                        <Chip 
                          label={`${Math.round(item.confianca * 100)}%`}
                          size="small" 
                          color={getConfidenceColor(item.confianca)}
                        />
                      </TableCell>
                      <TableCell>{formatDate(item.created_at)}</TableCell>
                      <TableCell>
                        <IconButton size="small" title="Editar">
                          <EditIcon />
                        </IconButton>
                        <IconButton size="small" title="Excluir" color="error">
                          <DeleteIcon />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </TabPanel>
      </Card>

      {/* Dialog para Novo Item */}
      <Dialog open={open} onClose={() => setOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Novo Item no Golden Set</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>Tipo</InputLabel>
                  <Select
                    value={formData.tipo}
                    onChange={(e) => setFormData({ ...formData, tipo: e.target.value as 'ncm' | 'cest' })}
                    label="Tipo"
                  >
                    <MenuItem value="ncm">NCM</MenuItem>
                    <MenuItem value="cest">CEST</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label={`Código ${formData.tipo.toUpperCase()}`}
                  value={formData.codigo}
                  onChange={(e) => setFormData({ ...formData, codigo: e.target.value })}
                  placeholder={formData.tipo === 'ncm' ? 'Ex: 8517.12.00' : 'Ex: 01.001.00'}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Descrição"
                  value={formData.descricao}
                  onChange={(e) => setFormData({ ...formData, descricao: e.target.value })}
                  multiline
                  rows={2}
                  placeholder="Descrição técnica do produto ou categoria"
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Categoria"
                  value={formData.categoria}
                  onChange={(e) => setFormData({ ...formData, categoria: e.target.value })}
                  placeholder="Ex: Eletrônicos, Medicamentos"
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Validado por"
                  value={formData.validado_por}
                  onChange={(e) => setFormData({ ...formData, validado_por: e.target.value })}
                  placeholder="Nome do validador"
                />
              </Grid>
            </Grid>
            <Alert severity="info" sx={{ mt: 2 }}>
              Items no Golden Set são usados como referência para melhorar a precisão das classificações automáticas.
            </Alert>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>Cancelar</Button>
          <Button 
            onClick={handleCreate} 
            variant="contained"
            disabled={creating || !formData.codigo || !formData.descricao || !formData.categoria}
          >
            {creating ? <CircularProgress size={20} /> : 'Adicionar ao Golden Set'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default GoldenSetPage;
