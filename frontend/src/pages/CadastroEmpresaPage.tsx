import React, { useState } from 'react';
import {
  Box, Paper, Typography, TextField, Button, Grid,
  FormControl, InputLabel, Select, MenuItem, Checkbox,
  FormControlLabel, Stepper, Step, StepLabel, Alert,
  Card, CardContent, Divider, Chip, IconButton,
  Table, TableBody, TableCell, TableContainer,
  TableHead, TableRow, Dialog, DialogTitle,
  DialogContent, DialogActions
} from '@mui/material';
import {
  Business, LocationOn, Phone, Email, Description,
  Add, Delete, Save, Cancel, CheckCircle
} from '@mui/icons-material';

interface AtividadeEconomica {
  cnae: string;
  descricao: string;
  principal: boolean;
}

interface DadosEmpresa {
  // Dados básicos
  razaoSocial: string;
  nomeFantasia: string;
  cnpj: string;
  inscricaoEstadual: string;
  inscricaoMunicipal: string;

  // Endereço
  cep: string;
  logradouro: string;
  numero: string;
  complemento: string;
  bairro: string;
  cidade: string;
  estado: string;

  // Contato
  telefone: string;
  email: string;
  responsavel: string;

  // Atividades econômicas
  atividades: AtividadeEconomica[];

  // Configurações
  regimeTributario: string;
  porteEmpresa: string;
  contribuinteICMS: boolean;
  contribuinteIPI: boolean;
  optanteSimples: boolean;
}

const CadastroEmpresaPage: React.FC = () => {
  const [activeStep, setActiveStep] = useState(0);
  const [dados, setDados] = useState<DadosEmpresa>({
    razaoSocial: '',
    nomeFantasia: '',
    cnpj: '',
    inscricaoEstadual: '',
    inscricaoMunicipal: '',
    cep: '',
    logradouro: '',
    numero: '',
    complemento: '',
    bairro: '',
    cidade: '',
    estado: '',
    telefone: '',
    email: '',
    responsavel: '',
    atividades: [],
    regimeTributario: '',
    porteEmpresa: '',
    contribuinteICMS: false,
    contribuinteIPI: false,
    optanteSimples: false
  });

  const [dialogAtividade, setDialogAtividade] = useState(false);
  const [novaAtividade, setNovaAtividade] = useState<AtividadeEconomica>({
    cnae: '',
    descricao: '',
    principal: false
  });
  const [salvando, setSalvando] = useState(false);
  const [sucesso, setSucesso] = useState(false);

  const steps = ['Dados Básicos', 'Endereço', 'Contato', 'Atividades', 'Configurações', 'Confirmação'];

  const handleInputChange = (field: keyof DadosEmpresa) => (
    event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    setDados(prev => ({
      ...prev,
      [field]: event.target.value
    }));
  };

  const handleSelectChange = (field: keyof DadosEmpresa) => (
    event: any
  ) => {
    setDados(prev => ({
      ...prev,
      [field]: event.target.value
    }));
  };

  const handleCheckboxChange = (field: keyof DadosEmpresa) => (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    setDados(prev => ({
      ...prev,
      [field]: event.target.checked
    }));
  };

  const buscarCEP = async (cep: string) => {
    if (cep.length === 8) {
      try {
        const response = await fetch(`https://viacep.com.br/ws/${cep}/json/`);
        const data = await response.json();

        if (!data.erro) {
          setDados(prev => ({
            ...prev,
            logradouro: data.logradouro,
            bairro: data.bairro,
            cidade: data.localidade,
            estado: data.uf
          }));
        }
      } catch (error) {
        console.error('Erro ao buscar CEP:', error);
      }
    }
  };

  const adicionarAtividade = () => {
    if (novaAtividade.cnae && novaAtividade.descricao) {
      // Se marcou como principal, desmarcar outras
      if (novaAtividade.principal) {
        setDados(prev => ({
          ...prev,
          atividades: [
            ...prev.atividades.map(a => ({ ...a, principal: false })),
            novaAtividade
          ]
        }));
      } else {
        setDados(prev => ({
          ...prev,
          atividades: [...prev.atividades, novaAtividade]
        }));
      }

      setNovaAtividade({ cnae: '', descricao: '', principal: false });
      setDialogAtividade(false);
    }
  };

  const removerAtividade = (index: number) => {
    setDados(prev => ({
      ...prev,
      atividades: prev.atividades.filter((_, i) => i !== index)
    }));
  };

  const salvarEmpresa = async () => {
    setSalvando(true);

    try {
      // Validação básica de campos obrigatórios
      if (!dados.razaoSocial || !dados.cnpj) {
        alert('Por favor, preencha pelo menos a Razão Social e CNPJ.');
        setSalvando(false);
        return;
      }

      const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      const endpoint = `${apiUrl}/empresas`;

      const requestData = {
        cnpj: dados.cnpj,
        razao_social: dados.razaoSocial,
        nome_fantasia: dados.nomeFantasia || dados.razaoSocial,
        atividade_principal: dados.atividades.find(a => a.principal)?.descricao || '',
        regime_tributario: dados.regimeTributario || 'Simples Nacional'
      };

      console.log('=== DEBUG CADASTRO EMPRESA ===');
      console.log('API URL:', apiUrl);
      console.log('Endpoint:', endpoint);
      console.log('Request Data:', requestData);

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData)
      });

      console.log('Response Status:', response.status);
      console.log('Response OK:', response.ok);

      if (response.ok) {
        const result = await response.json();
        console.log('Success Response:', result);
        setSucesso(true);
        setTimeout(() => {
          // Redirecionar para dashboard ou lista de empresas
          window.location.href = '/empresas';
        }, 2000);
      } else {
        const errorText = await response.text();
        console.log('Error Response Text:', errorText);

        let errorData;
        try {
          errorData = JSON.parse(errorText);
        } catch (e) {
          errorData = { detail: errorText };
        }

        throw new Error(errorData.detail || 'Erro ao salvar empresa');
      }
    } catch (error) {
      console.error('=== ERRO COMPLETO ===');
      console.error('Error:', error);
      console.error('Error message:', error instanceof Error ? error.message : 'Erro desconhecido');
      alert(`Erro ao salvar empresa: ${error instanceof Error ? error.message : 'Tente novamente.'}`);
    } finally {
      setSalvando(false);
    }
  };

  const renderStepContent = (step: number) => {
    switch (step) {
      case 0: // Dados Básicos
        return (
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Razão Social *"
                value={dados.razaoSocial}
                onChange={handleInputChange('razaoSocial')}
                required
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Nome Fantasia"
                value={dados.nomeFantasia}
                onChange={handleInputChange('nomeFantasia')}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="CNPJ *"
                value={dados.cnpj}
                onChange={handleInputChange('cnpj')}
                placeholder="00.000.000/0000-00"
                required
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Inscrição Estadual"
                value={dados.inscricaoEstadual}
                onChange={handleInputChange('inscricaoEstadual')}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Inscrição Municipal"
                value={dados.inscricaoMunicipal}
                onChange={handleInputChange('inscricaoMunicipal')}
              />
            </Grid>
          </Grid>
        );

      case 1: // Endereço
        return (
          <Grid container spacing={3}>
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="CEP *"
                value={dados.cep}
                onChange={(e) => {
                  handleInputChange('cep')(e);
                  buscarCEP(e.target.value.replace(/\D/g, ''));
                }}
                placeholder="00000-000"
                required
              />
            </Grid>
            <Grid item xs={12} md={8}>
              <TextField
                fullWidth
                label="Logradouro *"
                value={dados.logradouro}
                onChange={handleInputChange('logradouro')}
                required
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <TextField
                fullWidth
                label="Número *"
                value={dados.numero}
                onChange={handleInputChange('numero')}
                required
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <TextField
                fullWidth
                label="Complemento"
                value={dados.complemento}
                onChange={handleInputChange('complemento')}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Bairro *"
                value={dados.bairro}
                onChange={handleInputChange('bairro')}
                required
              />
            </Grid>
            <Grid item xs={12} md={8}>
              <TextField
                fullWidth
                label="Cidade *"
                value={dados.cidade}
                onChange={handleInputChange('cidade')}
                required
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <FormControl fullWidth required>
                <InputLabel>Estado</InputLabel>
                <Select
                  value={dados.estado}
                  onChange={handleSelectChange('estado')}
                >
                  <MenuItem value="AC">Acre</MenuItem>
                  <MenuItem value="AL">Alagoas</MenuItem>
                  <MenuItem value="AP">Amapá</MenuItem>
                  <MenuItem value="AM">Amazonas</MenuItem>
                  <MenuItem value="BA">Bahia</MenuItem>
                  <MenuItem value="CE">Ceará</MenuItem>
                  <MenuItem value="DF">Distrito Federal</MenuItem>
                  <MenuItem value="ES">Espírito Santo</MenuItem>
                  <MenuItem value="GO">Goiás</MenuItem>
                  <MenuItem value="MA">Maranhão</MenuItem>
                  <MenuItem value="MT">Mato Grosso</MenuItem>
                  <MenuItem value="MS">Mato Grosso do Sul</MenuItem>
                  <MenuItem value="MG">Minas Gerais</MenuItem>
                  <MenuItem value="PA">Pará</MenuItem>
                  <MenuItem value="PB">Paraíba</MenuItem>
                  <MenuItem value="PR">Paraná</MenuItem>
                  <MenuItem value="PE">Pernambuco</MenuItem>
                  <MenuItem value="PI">Piauí</MenuItem>
                  <MenuItem value="RJ">Rio de Janeiro</MenuItem>
                  <MenuItem value="RN">Rio Grande do Norte</MenuItem>
                  <MenuItem value="RS">Rio Grande do Sul</MenuItem>
                  <MenuItem value="RO">Rondônia</MenuItem>
                  <MenuItem value="RR">Roraima</MenuItem>
                  <MenuItem value="SC">Santa Catarina</MenuItem>
                  <MenuItem value="SP">São Paulo</MenuItem>
                  <MenuItem value="SE">Sergipe</MenuItem>
                  <MenuItem value="TO">Tocantins</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        );

      case 2: // Contato
        return (
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Telefone *"
                value={dados.telefone}
                onChange={handleInputChange('telefone')}
                placeholder="(00) 00000-0000"
                required
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="E-mail *"
                type="email"
                value={dados.email}
                onChange={handleInputChange('email')}
                required
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Responsável *"
                value={dados.responsavel}
                onChange={handleInputChange('responsavel')}
                placeholder="Nome do responsável pela empresa"
                required
              />
            </Grid>
          </Grid>
        );

      case 3: // Atividades
        return (
          <Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
              <Typography variant="h6">Atividades Econômicas (CNAE)</Typography>
              <Button
                variant="contained"
                startIcon={<Add />}
                onClick={() => setDialogAtividade(true)}
              >
                Adicionar Atividade
              </Button>
            </Box>

            {dados.atividades.length > 0 ? (
              <TableContainer component={Paper}>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>CNAE</TableCell>
                      <TableCell>Descrição</TableCell>
                      <TableCell>Principal</TableCell>
                      <TableCell>Ações</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {dados.atividades.map((atividade, index) => (
                      <TableRow key={index}>
                        <TableCell>{atividade.cnae}</TableCell>
                        <TableCell>{atividade.descricao}</TableCell>
                        <TableCell>
                          {atividade.principal && (
                            <Chip label="Principal" color="primary" size="small" />
                          )}
                        </TableCell>
                        <TableCell>
                          <IconButton
                            size="small"
                            color="error"
                            onClick={() => removerAtividade(index)}
                          >
                            <Delete />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            ) : (
              <Alert severity="info">
                Nenhuma atividade econômica cadastrada. Adicione pelo menos uma atividade.
              </Alert>
            )}
          </Box>
        );

      case 4: // Configurações
        return (
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth required>
                <InputLabel>Regime Tributário</InputLabel>
                <Select
                  value={dados.regimeTributario}
                  onChange={handleSelectChange('regimeTributario')}
                >
                  <MenuItem value="SIMPLES_NACIONAL">Simples Nacional</MenuItem>
                  <MenuItem value="LUCRO_PRESUMIDO">Lucro Presumido</MenuItem>
                  <MenuItem value="LUCRO_REAL">Lucro Real</MenuItem>
                  <MenuItem value="LUCRO_ARBITRADO">Lucro Arbitrado</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth required>
                <InputLabel>Porte da Empresa</InputLabel>
                <Select
                  value={dados.porteEmpresa}
                  onChange={handleSelectChange('porteEmpresa')}
                >
                  <MenuItem value="MEI">Microempreendedor Individual</MenuItem>
                  <MenuItem value="ME">Microempresa</MenuItem>
                  <MenuItem value="EPP">Empresa de Pequeno Porte</MenuItem>
                  <MenuItem value="MEDIA">Empresa de Médio Porte</MenuItem>
                  <MenuItem value="GRANDE">Grande Empresa</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Contribuições
              </Typography>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={dados.contribuinteICMS}
                    onChange={handleCheckboxChange('contribuinteICMS')}
                  />
                }
                label="Contribuinte de ICMS"
              />
              <FormControlLabel
                control={
                  <Checkbox
                    checked={dados.contribuinteIPI}
                    onChange={handleCheckboxChange('contribuinteIPI')}
                  />
                }
                label="Contribuinte de IPI"
              />
              <FormControlLabel
                control={
                  <Checkbox
                    checked={dados.optanteSimples}
                    onChange={handleCheckboxChange('optanteSimples')}
                  />
                }
                label="Optante pelo Simples Nacional"
              />
            </Grid>
          </Grid>
        );

      case 5: // Confirmação
        return (
          <Box>
            <Typography variant="h6" gutterBottom>
              Confirmar Dados da Empresa
            </Typography>

            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="subtitle1" gutterBottom>
                      <Business sx={{ mr: 1, verticalAlign: 'middle' }} />
                      Dados Básicos
                    </Typography>
                    <Typography variant="body2">
                      <strong>Razão Social:</strong> {dados.razaoSocial}
                    </Typography>
                    <Typography variant="body2">
                      <strong>CNPJ:</strong> {dados.cnpj}
                    </Typography>
                    {dados.inscricaoEstadual && (
                      <Typography variant="body2">
                        <strong>IE:</strong> {dados.inscricaoEstadual}
                      </Typography>
                    )}
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="subtitle1" gutterBottom>
                      <LocationOn sx={{ mr: 1, verticalAlign: 'middle' }} />
                      Endereço
                    </Typography>
                    <Typography variant="body2">
                      {dados.logradouro}, {dados.numero}
                    </Typography>
                    <Typography variant="body2">
                      {dados.bairro} - {dados.cidade}/{dados.estado}
                    </Typography>
                    <Typography variant="body2">
                      CEP: {dados.cep}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="subtitle1" gutterBottom>
                      <Phone sx={{ mr: 1, verticalAlign: 'middle' }} />
                      Contato
                    </Typography>
                    <Typography variant="body2">
                      <strong>Responsável:</strong> {dados.responsavel}
                    </Typography>
                    <Typography variant="body2">
                      <strong>Telefone:</strong> {dados.telefone}
                    </Typography>
                    <Typography variant="body2">
                      <strong>E-mail:</strong> {dados.email}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="subtitle1" gutterBottom>
                      <Description sx={{ mr: 1, verticalAlign: 'middle' }} />
                      Configurações
                    </Typography>
                    <Typography variant="body2">
                      <strong>Regime:</strong> {dados.regimeTributario}
                    </Typography>
                    <Typography variant="body2">
                      <strong>Porte:</strong> {dados.porteEmpresa}
                    </Typography>
                    <Typography variant="body2">
                      <strong>Atividades:</strong> {dados.atividades.length} cadastrada(s)
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Box>
        );

      default:
        return null;
    }
  };

  if (sucesso) {
    return (
      <Box sx={{ maxWidth: 600, mx: 'auto', p: 3, textAlign: 'center' }}>
        <CheckCircle sx={{ fontSize: 64, color: 'success.main', mb: 2 }} />
        <Typography variant="h4" gutterBottom>
          Empresa Cadastrada com Sucesso!
        </Typography>
        <Typography variant="body1" color="textSecondary">
          Os dados da empresa foram salvos e o sistema está configurando o ambiente.
          Você será redirecionado em alguns segundos...
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ maxWidth: 1000, mx: 'auto', p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Cadastro de Nova Empresa
      </Typography>

      <Paper sx={{ p: 3 }}>
        <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
          {steps.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>

        <Box sx={{ minHeight: 400 }}>
          {renderStepContent(activeStep)}
        </Box>

        <Divider sx={{ my: 3 }} />

        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
          <Button
            variant="outlined"
            onClick={() => setActiveStep(prev => Math.max(0, prev - 1))}
            disabled={activeStep === 0}
            startIcon={<Cancel />}
          >
            Voltar
          </Button>

          <Box>
            {activeStep === steps.length - 1 ? (
              <Button
                variant="contained"
                onClick={salvarEmpresa}
                disabled={salvando || !dados.razaoSocial || !dados.cnpj}
                startIcon={<Save />}
                size="large"
              >
                {salvando ? 'Salvando...' : 'Finalizar Cadastro'}
              </Button>
            ) : (
              <Button
                variant="contained"
                onClick={() => setActiveStep(prev => prev + 1)}
                disabled={
                  (activeStep === 0 && (!dados.razaoSocial || !dados.cnpj)) ||
                  (activeStep === 2 && !dados.email)
                }
              >
                Próximo
              </Button>
            )}
          </Box>
        </Box>
      </Paper>

      {/* Dialog para adicionar atividade */}
      <Dialog open={dialogAtividade} onClose={() => setDialogAtividade(false)} maxWidth="md" fullWidth>
        <DialogTitle>Adicionar Atividade Econômica</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="Código CNAE"
                value={novaAtividade.cnae}
                onChange={(e) => setNovaAtividade(prev => ({ ...prev, cnae: e.target.value }))}
                placeholder="0000-0/00"
              />
            </Grid>
            <Grid item xs={12} md={8}>
              <TextField
                fullWidth
                label="Descrição da Atividade"
                value={novaAtividade.descricao}
                onChange={(e) => setNovaAtividade(prev => ({ ...prev, descricao: e.target.value }))}
              />
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={novaAtividade.principal}
                    onChange={(e) => setNovaAtividade(prev => ({ ...prev, principal: e.target.checked }))}
                  />
                }
                label="Atividade Principal"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogAtividade(false)}>
            Cancelar
          </Button>
          <Button variant="contained" onClick={adicionarAtividade}>
            Adicionar
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default CadastroEmpresaPage;
