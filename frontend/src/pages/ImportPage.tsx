import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Grid,
  Stepper,
  Step,
  StepLabel,
  Alert,
  CircularProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
} from '@mui/material';
import {
  ExpandMore,
  Storage,
  Preview,
  CloudUpload,
  CheckCircle,
  Error,
  Info,
} from '@mui/icons-material';
import { importService, DatabaseConnection, ConnectionTestResult, DataPreview, ImportResult } from '../services/importService';

const steps = ['Configuração', 'Conexão', 'Preview', 'Importação'];

interface ImportPageProps {}

const ImportPage: React.FC<ImportPageProps> = () => {
  // Estados do Stepper
  const [activeStep, setActiveStep] = useState(0);
  const [completed, setCompleted] = useState<{ [k: number]: boolean }>({});

  // Estados da conexão
  const [connection, setConnection] = useState<DatabaseConnection>({
    type: 'postgresql',
    host: 'localhost',
    port: 5432,
    database: 'db_04565289005297',
    user: 'postgres',
    password: 'sefin',
    schema: 'dbo'
  });

  // Estados de operação
  const [loading, setLoading] = useState(false);
  const [connectionResult, setConnectionResult] = useState<ConnectionTestResult | null>(null);
  const [previewData, setPreviewData] = useState<DataPreview | null>(null);
  const [importResult, setImportResult] = useState<ImportResult | null>(null);
  const [sqlQuery, setSqlQuery] = useState('');
  const [error, setError] = useState<string | null>(null);

  // Estados da API
  const [apiHealth, setApiHealth] = useState<any>(null);
  const [systemStats, setSystemStats] = useState<any>(null);

  // Verificar saúde da API ao carregar
  useEffect(() => {
    checkApiHealth();
    loadSystemStats();
  }, []);

  // Atualizar query SQL quando tipo de banco muda
  useEffect(() => {
    const presets = importService.getPresetQueries();
    setSqlQuery(presets[connection.type]?.complete || '');
  }, [connection.type]);

  const checkApiHealth = async () => {
    try {
      const health = await importService.checkHealth();
      setApiHealth(health);
    } catch (error) {
      console.error('Erro ao verificar API:', error);
      setError('Não foi possível conectar com a API. Verifique se está rodando em http://localhost:8003');
    }
  };

  const loadSystemStats = async () => {
    try {
      const stats = await importService.getSystemStats();
      setSystemStats(stats);
    } catch (error) {
      console.error('Erro ao carregar estatísticas:', error);
    }
  };

  const handleNext = () => {
    setActiveStep((prevActiveStep) => prevActiveStep + 1);
  };

  const handleBack = () => {
    setActiveStep((prevActiveStep) => prevActiveStep - 1);
  };

  const handleStep = (step: number) => () => {
    setActiveStep(step);
  };

  const handleTestConnection = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await importService.testConnection(connection);
      setConnectionResult(result);
      if (result.success) {
        setCompleted({ ...completed, 1: true });
      }
    } catch (error: any) {
      setError('Erro ao testar conexão: ' + (error.message || 'Erro desconhecido'));
    }
    setLoading(false);
  };

  const handlePreview = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await importService.previewData(connection, sqlQuery, 10);
      setPreviewData(result);
      if (result.success) {
        setCompleted({ ...completed, 2: true });
      }
    } catch (error: any) {
      setError('Erro no preview: ' + (error.message || 'Erro desconhecido'));
    }
    setLoading(false);
  };

  const handleImport = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await importService.executeImport(connection, sqlQuery);
      setImportResult(result);
      if (result.success) {
        setCompleted({ ...completed, 3: true });
        await loadSystemStats(); // Atualizar estatísticas
      }
    } catch (error: any) {
      setError('Erro na importação: ' + (error.message || 'Erro desconhecido'));
    }
    setLoading(false);
  };

  const renderStepContent = (step: number) => {
    switch (step) {
      case 0:
        return (
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Configuração da Conexão
              </Typography>
            </Grid>

            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Tipo de Banco</InputLabel>
                <Select
                  value={connection.type}
                  label="Tipo de Banco"
                  onChange={(e) => setConnection({ ...connection, type: e.target.value as any })}
                >
                  <MenuItem value="postgresql">PostgreSQL</MenuItem>
                  <MenuItem value="sqlserver">SQL Server</MenuItem>
                  <MenuItem value="mysql">MySQL</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Host"
                value={connection.host}
                onChange={(e) => setConnection({ ...connection, host: e.target.value })}
              />
            </Grid>

            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Porta"
                type="number"
                value={connection.port}
                onChange={(e) => setConnection({ ...connection, port: parseInt(e.target.value) })}
              />
            </Grid>

            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Database"
                value={connection.database}
                onChange={(e) => setConnection({ ...connection, database: e.target.value })}
              />
            </Grid>

            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Usuário"
                value={connection.user}
                onChange={(e) => setConnection({ ...connection, user: e.target.value })}
              />
            </Grid>

            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Senha"
                type="password"
                value={connection.password}
                onChange={(e) => setConnection({ ...connection, password: e.target.value })}
              />
            </Grid>

            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Schema (opcional)"
                value={connection.schema || ''}
                onChange={(e) => setConnection({ ...connection, schema: e.target.value })}
              />
            </Grid>

            <Grid item xs={12}>
              <Button
                variant="contained"
                onClick={handleNext}
                startIcon={<Storage />}
              >
                Prosseguir para Teste de Conexão
              </Button>
            </Grid>
          </Grid>
        );

      case 1:
        return (
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Teste de Conexão
              </Typography>
              <Alert severity="info" sx={{ mb: 2 }}>
                Verifique se a conexão com o banco de dados está funcionando corretamente.
              </Alert>
            </Grid>

            <Grid item xs={12}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="subtitle1" gutterBottom>
                    Configuração Atual:
                  </Typography>
                  <Typography variant="body2">
                    <strong>Tipo:</strong> {connection.type.toUpperCase()}<br />
                    <strong>Host:</strong> {connection.host}:{connection.port}<br />
                    <strong>Database:</strong> {connection.database}<br />
                    <strong>Usuário:</strong> {connection.user}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            {connectionResult && (
              <Grid item xs={12}>
                <Alert
                  severity={connectionResult.success ? 'success' : 'error'}
                  icon={connectionResult.success ? <CheckCircle /> : <Error />}
                >
                  {connectionResult.success ? (
                    <div>
                      <Typography variant="subtitle2">Conexão bem-sucedida!</Typography>
                      <Typography variant="body2">
                        Database: {connectionResult.database}<br />
                        Host: {connectionResult.host}<br />
                        Info: {connectionResult.database_info?.substring(0, 100)}...
                      </Typography>
                    </div>
                  ) : (
                    <div>
                      <Typography variant="subtitle2">Falha na conexão</Typography>
                      <Typography variant="body2">
                        {connectionResult.error || connectionResult.message}
                      </Typography>
                    </div>
                  )}
                </Alert>
              </Grid>
            )}

            <Grid item xs={12}>
              <Box sx={{ display: 'flex', gap: 2 }}>
                <Button onClick={handleBack}>
                  Voltar
                </Button>
                <Button
                  variant="contained"
                  onClick={handleTestConnection}
                  disabled={loading}
                  startIcon={loading ? <CircularProgress size={20} /> : <Storage />}
                >
                  {loading ? 'Testando...' : 'Testar Conexão'}
                </Button>
                {connectionResult?.success && (
                  <Button
                    variant="contained"
                    color="success"
                    onClick={handleNext}
                    startIcon={<Preview />}
                  >
                    Prosseguir para Preview
                  </Button>
                )}
              </Box>
            </Grid>
          </Grid>
        );

      case 2:
        return (
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Preview dos Dados
              </Typography>
              <Alert severity="info" sx={{ mb: 2 }}>
                Configure a consulta SQL e visualize uma amostra dos dados antes da importação.
              </Alert>
            </Grid>

            <Grid item xs={12}>
              <TextField
                fullWidth
                multiline
                rows={8}
                label="Consulta SQL"
                value={sqlQuery}
                onChange={(e) => setSqlQuery(e.target.value)}
                helperText="SQL query para extrair os dados. Use LIMIT para controlar o volume."
              />
            </Grid>

            {previewData && (
              <Grid item xs={12}>
                <Accordion defaultExpanded>
                  <AccordionSummary expandIcon={<ExpandMore />}>
                    <Typography variant="h6">
                      Resultado do Preview
                      <Chip
                        label={`${previewData.preview_count} registros`}
                        color="primary"
                        size="small"
                        sx={{ ml: 2 }}
                      />
                    </Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    {previewData.success ? (
                      <div>
                        <Typography variant="subtitle2" gutterBottom>
                          Colunas encontradas: {previewData.columns.join(', ')}
                        </Typography>
                        <TableContainer component={Paper} sx={{ mt: 2 }}>
                          <Table size="small">
                            <TableHead>
                              <TableRow>
                                {previewData.columns.map((col) => (
                                  <TableCell key={col}><strong>{col}</strong></TableCell>
                                ))}
                              </TableRow>
                            </TableHead>
                            <TableBody>
                              {previewData.data.slice(0, 5).map((row, index) => (
                                <TableRow key={index}>
                                  {previewData.columns.map((col) => (
                                    <TableCell key={col}>
                                      {String(row[col] || '').substring(0, 50)}
                                      {String(row[col] || '').length > 50 ? '...' : ''}
                                    </TableCell>
                                  ))}
                                </TableRow>
                              ))}
                            </TableBody>
                          </Table>
                        </TableContainer>
                      </div>
                    ) : (
                      <Alert severity="error">
                        Erro no preview: {previewData.error}
                      </Alert>
                    )}
                  </AccordionDetails>
                </Accordion>
              </Grid>
            )}

            <Grid item xs={12}>
              <Box sx={{ display: 'flex', gap: 2 }}>
                <Button onClick={handleBack}>
                  Voltar
                </Button>
                <Button
                  variant="contained"
                  onClick={handlePreview}
                  disabled={loading || !sqlQuery.trim()}
                  startIcon={loading ? <CircularProgress size={20} /> : <Preview />}
                >
                  {loading ? 'Carregando...' : 'Fazer Preview'}
                </Button>
                {previewData?.success && (
                  <Button
                    variant="contained"
                    color="success"
                    onClick={handleNext}
                    startIcon={<CloudUpload />}
                  >
                    Prosseguir para Importação
                  </Button>
                )}
              </Box>
            </Grid>
          </Grid>
        );

      case 3:
        return (
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Importação Final
              </Typography>
              <Alert severity="warning" sx={{ mb: 2 }}>
                Esta operação irá importar os dados para o sistema. Certifique-se de que os dados estão corretos.
              </Alert>
            </Grid>

            {importResult && (
              <Grid item xs={12}>
                <Alert
                  severity={importResult.success ? 'success' : 'error'}
                  icon={importResult.success ? <CheckCircle /> : <Error />}
                >
                  {importResult.success ? (
                    <div>
                      <Typography variant="subtitle2">Importação concluída com sucesso!</Typography>
                      <Typography variant="body2">
                        <strong>Registros importados:</strong> {importResult.records_imported}<br />
                        <strong>Registros com erro:</strong> {importResult.records_with_errors}<br />
                        <strong>Tempo de execução:</strong> {importResult.execution_time.toFixed(2)}s<br />
                        <strong>Empresas:</strong> {importResult.summary.empresas}<br />
                        <strong>Produtos:</strong> {importResult.summary.produtos}<br />
                        <strong>NCM matches:</strong> {importResult.summary.ncm_matches}<br />
                        <strong>CEST matches:</strong> {importResult.summary.cest_matches}
                      </Typography>
                    </div>
                  ) : (
                    <div>
                      <Typography variant="subtitle2">Falha na importação</Typography>
                      <Typography variant="body2">
                        Verifique os logs para mais detalhes.
                      </Typography>
                    </div>
                  )}
                </Alert>
              </Grid>
            )}

            <Grid item xs={12}>
              <Box sx={{ display: 'flex', gap: 2 }}>
                <Button onClick={handleBack}>
                  Voltar
                </Button>
                <Button
                  variant="contained"
                  color="primary"
                  onClick={handleImport}
                  disabled={loading}
                  startIcon={loading ? <CircularProgress size={20} /> : <CloudUpload />}
                >
                  {loading ? 'Importando...' : 'Executar Importação'}
                </Button>
              </Box>
            </Grid>
          </Grid>
        );

      default:
        return 'Etapa desconhecida';
    }
  };

  return (
    <Box sx={{ width: '100%', p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Importação de Dados
      </Typography>

      {/* Status da API */}
      <Grid container spacing={2} sx={{ mb: 4 }}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Status da API
              </Typography>
              {apiHealth ? (
                <Box>
                  <Chip
                    label={`${apiHealth.status} - v${apiHealth.version}`}
                    color="success"
                    icon={<CheckCircle />}
                  />
                  <Typography variant="body2" sx={{ mt: 1 }}>
                    Conectado em: http://localhost:8003
                  </Typography>
                </Box>
              ) : (
                <Chip
                  label="Desconectado"
                  color="error"
                  icon={<Error />}
                />
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Estatísticas do Sistema
              </Typography>
              {systemStats ? (
                <Box>
                  <Typography variant="body2">
                    <strong>Empresas:</strong> {systemStats.total_empresas}<br />
                    <strong>Produtos:</strong> {systemStats.total_produtos}<br />
                    <strong>Status:</strong> {systemStats.status}
                  </Typography>
                </Box>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  Carregando...
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Stepper */}
      <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
        {steps.map((label, index) => (
          <Step key={label} completed={completed[index]}>
            <StepLabel
              onClick={handleStep(index)}
              sx={{ cursor: 'pointer' }}
            >
              {label}
            </StepLabel>
          </Step>
        ))}
      </Stepper>

      {/* Erro global */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Conteúdo da etapa */}
      <Card>
        <CardContent>
          {renderStepContent(activeStep)}
        </CardContent>
      </Card>
    </Box>
  );
};

export default ImportPage;
