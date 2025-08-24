import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  TextField,
  Grid,
  Card,
  CardContent,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  LinearProgress,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Tooltip,
  IconButton,
  Stepper,
  Step,
  StepLabel,
  CircularProgress,
  Divider,
  Breadcrumbs,
  Link as MuiLink
} from '@mui/material';
import {
  Upload as UploadIcon,
  Download as DownloadIcon,
  Preview as PreviewIcon,
  Check as CheckIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  Refresh as RefreshIcon,
  Storage as StorageIcon,
  TableChart as TableIcon,
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Home as HomeIcon,
  Business as BusinessIcon,
  CloudUpload as CloudUploadIcon
} from '@mui/icons-material';
import { useParams, Link, useNavigate } from 'react-router-dom';
import axios from 'axios';

interface DatabaseConnection {
  type: string;
  host: string;
  port: number;
  database: string;
  schema: string;
  user: string;
  password: string;
}

interface ImportConfig {
  empresa_id: number;
  sql_query: string;
  connection: DatabaseConnection;
  batch_size: number;
  update_existing: boolean;
}

interface PreviewData {
  columns: string[];
  rows: any[][];
  total_count: number;
  sample_size: number;
}

interface ImportJob {
  job_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  total_records: number;
  processed_records: number;
  error_message?: string;
  start_time: string;
  end_time?: string;
}

const ImportacaoPage: React.FC = () => {
  const { empresaId } = useParams<{ empresaId: string }>();
  const navigate = useNavigate();

  // Estados
  const [activeStep, setActiveStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [empresa, setEmpresa] = useState<any>(null);
  const [importConfig, setImportConfig] = useState<ImportConfig>({
    empresa_id: parseInt(empresaId || '0'),
    sql_query: `SELECT
                produto_id,
                descricao_produto,
                codigo_produto,
                codigo_barra,
                ncm,
                cest,
                DENSE_RANK() OVER (ORDER BY descricao_produto) AS id_agregados,
                COUNT(*) OVER (PARTITION BY descricao_produto) AS qtd_mesma_desc
            FROM dbo.produto
            WHERE descricao_produto IS NOT NULL`,
    connection: {
      type: 'sqlserver',
      host: 'localhost',
      port: 1433,
      database: 'db_04565289005297',
      schema: 'dbo',
      user: 'postgres',
      password: 'sefin'
    },
    batch_size: 1000,
    update_existing: false
  });
  const [previewData, setPreviewData] = useState<PreviewData | null>(null);
  const [importJob, setImportJob] = useState<ImportJob | null>(null);
  const [connectionTest, setConnectionTest] = useState<{
    status: 'idle' | 'testing' | 'success' | 'error';
    message: string;
  }>({ status: 'idle', message: '' });

  const steps = [
    'Configurar Conexão',
    'Visualizar Dados',
    'Confirmar Importação',
    'Executar Import'
  ];

  // Carregar dados da empresa
  useEffect(() => {
    const fetchEmpresa = async () => {
      try {
        const response = await axios.get(`/api/empresas/${empresaId}`);
        setEmpresa(response.data);
      } catch (error) {
        console.error('Erro ao carregar empresa:', error);
      }
    };

    if (empresaId) {
      fetchEmpresa();
    }
  }, [empresaId]);

  // Testar conexão com banco
  const testConnection = async () => {
    setConnectionTest({ status: 'testing', message: 'Testando conexão...' });

    try {
      const response = await axios.post('/api/import/test-connection', {
        connection: importConfig.connection
      });

      if (response.data.success) {
        setConnectionTest({
          status: 'success',
          message: `Conexão estabelecida! ${response.data.database_info}`
        });
      } else {
        setConnectionTest({
          status: 'error',
          message: response.data.error || 'Erro na conexão'
        });
      }
    } catch (error: any) {
      setConnectionTest({
        status: 'error',
        message: error.response?.data?.detail || 'Erro ao testar conexão'
      });
    }
  };

  // Preview dos dados
  const previewImport = async () => {
    setLoading(true);
    try {
      const response = await axios.post('/api/import/preview', {
        connection: importConfig.connection,
        sql_query: importConfig.sql_query,
        limit: 100
      });

      setPreviewData(response.data);
      setActiveStep(1);
    } catch (error: any) {
      console.error('Erro no preview:', error);
      alert(error.response?.data?.detail || 'Erro ao fazer preview dos dados');
    } finally {
      setLoading(false);
    }
  };

  // Executar importação
  const executeImport = async () => {
    setLoading(true);
    try {
      const response = await axios.post('/api/import/execute', importConfig);
      setImportJob(response.data);
      setActiveStep(3);

      // Polling do status
      pollImportStatus(response.data.job_id);
    } catch (error: any) {
      console.error('Erro na importação:', error);
      alert(error.response?.data?.detail || 'Erro ao executar importação');
    } finally {
      setLoading(false);
    }
  };

  // Polling do status da importação
  const pollImportStatus = async (jobId: string) => {
    const checkStatus = async () => {
      try {
        const response = await axios.get(`/api/import/status/${jobId}`);
        setImportJob(response.data);

        if (response.data.status === 'running') {
          setTimeout(checkStatus, 2000); // Check a cada 2 segundos
        }
      } catch (error) {
        console.error('Erro ao verificar status:', error);
      }
    };

    checkStatus();
  };

  const handleNext = () => {
    if (activeStep === 0 && connectionTest.status !== 'success') {
      alert('Teste a conexão antes de continuar');
      return;
    }

    if (activeStep === 1) {
      setActiveStep(2);
    } else if (activeStep === 2) {
      executeImport();
    }
  };

  const handleBack = () => {
    setActiveStep(Math.max(0, activeStep - 1));
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Breadcrumbs */}
      <Breadcrumbs sx={{ mb: 3 }}>
        <MuiLink component={Link} to="/dashboard" sx={{ display: 'flex', alignItems: 'center' }}>
          <HomeIcon sx={{ mr: 0.5 }} fontSize="inherit" />
          Dashboard
        </MuiLink>
        <MuiLink component={Link} to="/empresas" sx={{ display: 'flex', alignItems: 'center' }}>
          <BusinessIcon sx={{ mr: 0.5 }} fontSize="inherit" />
          Empresas
        </MuiLink>
        <Typography color="text.primary" sx={{ display: 'flex', alignItems: 'center' }}>
          <CloudUploadIcon sx={{ mr: 0.5 }} fontSize="inherit" />
          Importação de Dados
        </Typography>
      </Breadcrumbs>

      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <CloudUploadIcon color="primary" sx={{ fontSize: 40 }} />
          Importação de Produtos
        </Typography>
        {empresa && (
          <Typography variant="h6" color="text.secondary">
            Empresa: {empresa.nome} | CNPJ: {empresa.cnpj}
          </Typography>
        )}
      </Box>

      {/* Stepper */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Stepper activeStep={activeStep} alternativeLabel>
          {steps.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>
      </Paper>

      {/* Step 0: Configuração da Conexão */}
      {activeStep === 0 && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <StorageIcon />
            Configuração da Conexão com Banco de Dados
          </Typography>

          <Grid container spacing={3} sx={{ mt: 2 }}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Tipo de Banco"
                value={importConfig.connection.type}
                onChange={(e) => setImportConfig(prev => ({
                  ...prev,
                  connection: { ...prev.connection, type: e.target.value }
                }))}
                select
              >
                <MenuItem value="sqlserver">SQL Server</MenuItem>
                <MenuItem value="postgresql">PostgreSQL</MenuItem>
                <MenuItem value="mysql">MySQL</MenuItem>
              </TextField>
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Host"
                value={importConfig.connection.host}
                onChange={(e) => setImportConfig(prev => ({
                  ...prev,
                  connection: { ...prev.connection, host: e.target.value }
                }))}
              />
            </Grid>

            <Grid item xs={12} md={3}>
              <TextField
                fullWidth
                label="Porta"
                type="number"
                value={importConfig.connection.port}
                onChange={(e) => setImportConfig(prev => ({
                  ...prev,
                  connection: { ...prev.connection, port: parseInt(e.target.value) }
                }))}
              />
            </Grid>

            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="Banco de Dados"
                value={importConfig.connection.database}
                onChange={(e) => setImportConfig(prev => ({
                  ...prev,
                  connection: { ...prev.connection, database: e.target.value }
                }))}
              />
            </Grid>

            <Grid item xs={12} md={2}>
              <TextField
                fullWidth
                label="Schema"
                value={importConfig.connection.schema}
                onChange={(e) => setImportConfig(prev => ({
                  ...prev,
                  connection: { ...prev.connection, schema: e.target.value }
                }))}
              />
            </Grid>

            <Grid item xs={12} md={3}>
              <TextField
                fullWidth
                label="Usuário"
                value={importConfig.connection.user}
                onChange={(e) => setImportConfig(prev => ({
                  ...prev,
                  connection: { ...prev.connection, user: e.target.value }
                }))}
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Senha"
                type="password"
                value={importConfig.connection.password}
                onChange={(e) => setImportConfig(prev => ({
                  ...prev,
                  connection: { ...prev.connection, password: e.target.value }
                }))}
              />
            </Grid>

            <Grid item xs={12}>
              <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
                <Button
                  variant="outlined"
                  onClick={testConnection}
                  disabled={connectionTest.status === 'testing'}
                  startIcon={connectionTest.status === 'testing' ? <CircularProgress size={20} /> : <RefreshIcon />}
                >
                  Testar Conexão
                </Button>

                {connectionTest.status !== 'idle' && (
                  <Alert
                    severity={connectionTest.status === 'success' ? 'success' : connectionTest.status === 'error' ? 'error' : 'info'}
                    sx={{ flex: 1 }}
                  >
                    {connectionTest.message}
                  </Alert>
                )}
              </Box>
            </Grid>

            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Query SQL"
                multiline
                rows={8}
                value={importConfig.sql_query}
                onChange={(e) => setImportConfig(prev => ({
                  ...prev,
                  sql_query: e.target.value
                }))}
                helperText="Digite a query SQL para extrair os produtos a serem importados"
              />
            </Grid>
          </Grid>

          <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 3 }}>
            <Button onClick={() => navigate(-1)}>
              Cancelar
            </Button>
            <Button
              variant="contained"
              onClick={previewImport}
              disabled={loading || connectionTest.status !== 'success'}
              startIcon={loading ? <CircularProgress size={20} /> : <PreviewIcon />}
            >
              Visualizar Dados
            </Button>
          </Box>
        </Paper>
      )}

      {/* Step 1: Preview dos Dados */}
      {activeStep === 1 && previewData && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <TableIcon />
            Preview dos Dados
          </Typography>

          <Alert severity="info" sx={{ mb: 3 }}>
            Mostrando {previewData.sample_size} de {previewData.total_count} registros totais
          </Alert>

          <TableContainer sx={{ maxHeight: 400 }}>
            <Table stickyHeader>
              <TableHead>
                <TableRow>
                  {previewData.columns.map((column) => (
                    <TableCell key={column}>{column}</TableCell>
                  ))}
                </TableRow>
              </TableHead>
              <TableBody>
                {previewData.rows.map((row, index) => (
                  <TableRow key={index}>
                    {row.map((cell, cellIndex) => (
                      <TableCell key={cellIndex}>{cell}</TableCell>
                    ))}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>

          <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 3 }}>
            <Button onClick={handleBack}>
              Voltar
            </Button>
            <Button variant="contained" onClick={handleNext}>
              Continuar
            </Button>
          </Box>
        </Paper>
      )}

      {/* Step 2: Configurações da Importação */}
      {activeStep === 2 && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <InfoIcon />
            Configurações da Importação
          </Typography>

          <Grid container spacing={3} sx={{ mt: 2 }}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Tamanho do Lote"
                type="number"
                value={importConfig.batch_size}
                onChange={(e) => setImportConfig(prev => ({
                  ...prev,
                  batch_size: parseInt(e.target.value)
                }))}
                helperText="Número de registros processados por vez"
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Atualizar Existentes</InputLabel>
                <Select
                  value={importConfig.update_existing ? 'true' : 'false'}
                  onChange={(e) => setImportConfig(prev => ({
                    ...prev,
                    update_existing: e.target.value === 'true'
                  }))}
                >
                  <MenuItem value="false">Não - Apenas novos registros</MenuItem>
                  <MenuItem value="true">Sim - Atualizar registros existentes</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>

          <Alert severity="warning" sx={{ mt: 3 }}>
            <Typography variant="body2">
              <strong>Atenção:</strong> Esta operação irá importar {previewData?.total_count} registros.
              {importConfig.update_existing && ' Registros existentes serão atualizados.'}
            </Typography>
          </Alert>

          <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 3 }}>
            <Button onClick={handleBack}>
              Voltar
            </Button>
            <Button
              variant="contained"
              color="primary"
              onClick={handleNext}
              startIcon={<PlayIcon />}
            >
              Executar Importação
            </Button>
          </Box>
        </Paper>
      )}

      {/* Step 3: Execução da Importação */}
      {activeStep === 3 && importJob && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {importJob.status === 'completed' ? <CheckIcon color="success" /> :
             importJob.status === 'failed' ? <ErrorIcon color="error" /> :
             <CircularProgress size={24} />}
            Status da Importação
          </Typography>

          <Card sx={{ mt: 2 }}>
            <CardContent>
              <Grid container spacing={2}>
                <Grid item xs={12} md={3}>
                  <Typography variant="body2" color="text.secondary">
                    Status
                  </Typography>
                  <Chip
                    label={importJob.status}
                    color={
                      importJob.status === 'completed' ? 'success' :
                      importJob.status === 'failed' ? 'error' :
                      importJob.status === 'running' ? 'warning' : 'default'
                    }
                  />
                </Grid>

                <Grid item xs={12} md={3}>
                  <Typography variant="body2" color="text.secondary">
                    Progresso
                  </Typography>
                  <Typography variant="body1">
                    {importJob.processed_records} / {importJob.total_records}
                  </Typography>
                </Grid>

                <Grid item xs={12} md={3}>
                  <Typography variant="body2" color="text.secondary">
                    Início
                  </Typography>
                  <Typography variant="body1">
                    {new Date(importJob.start_time).toLocaleString()}
                  </Typography>
                </Grid>

                <Grid item xs={12} md={3}>
                  <Typography variant="body2" color="text.secondary">
                    Fim
                  </Typography>
                  <Typography variant="body1">
                    {importJob.end_time ? new Date(importJob.end_time).toLocaleString() : '-'}
                  </Typography>
                </Grid>
              </Grid>

              {importJob.total_records > 0 && (
                <Box sx={{ mt: 2 }}>
                  <LinearProgress
                    variant="determinate"
                    value={(importJob.processed_records / importJob.total_records) * 100}
                  />
                </Box>
              )}

              {importJob.error_message && (
                <Alert severity="error" sx={{ mt: 2 }}>
                  {importJob.error_message}
                </Alert>
              )}
            </CardContent>
          </Card>

          <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 3 }}>
            <Button onClick={() => navigate('/empresas')}>
              Voltar para Empresas
            </Button>
            {importJob.status === 'completed' && (
              <Button
                variant="contained"
                onClick={() => navigate(`/empresas/${empresaId}/produtos`)}
                startIcon={<CheckIcon />}
              >
                Ver Produtos Importados
              </Button>
            )}
          </Box>
        </Paper>
      )}
    </Box>
  );
};

export default ImportacaoPage;
