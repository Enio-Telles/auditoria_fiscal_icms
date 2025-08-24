import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Button,
  Typography,
  Card,
  CardContent,
  Grid,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Chip,
  Divider,
  Alert,
  LinearProgress,
} from '@mui/material';
import {
  PlayArrow as PlayIcon,
  CheckCircle as CheckIcon,
  Info as InfoIcon,
  School as SchoolIcon,
  Business as BusinessIcon,
  Upload as UploadIcon,
  SmartToy as AIIcon,
  Assessment as ReportIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material';

interface OnboardingStep {
  id: number;
  title: string;
  description: string;
  content: React.ReactNode;
  action?: () => void;
  completed?: boolean;
}

const OnboardingPage: React.FC = () => {
  const [activeStep, setActiveStep] = useState(0);
  const [completedSteps, setCompletedSteps] = useState<number[]>([]);
  const [showDemo, setShowDemo] = useState(false);
  const [demoType, setDemoType] = useState<string>('');
  const [progress, setProgress] = useState(0);

  const handleStepComplete = (stepId: number) => {
    if (!completedSteps.includes(stepId)) {
      setCompletedSteps([...completedSteps, stepId]);
    }
  };

  const handleNext = () => {
    handleStepComplete(activeStep);
    setActiveStep((prevActiveStep) => prevActiveStep + 1);
  };

  const handleBack = () => {
    setActiveStep((prevActiveStep) => prevActiveStep - 1);
  };

  const startDemo = (type: string) => {
    setDemoType(type);
    setShowDemo(true);
  };

  useEffect(() => {
    const totalSteps = 6;
    const completed = completedSteps.length;
    setProgress((completed / totalSteps) * 100);
  }, [completedSteps]);

  const steps: OnboardingStep[] = [
    {
      id: 0,
      title: "Bem-vindo ao Sistema de Auditoria Fiscal ICMS",
      description: "Conheça as principais funcionalidades do sistema",
      content: (
        <Box>
          <Typography variant="h6" gutterBottom>
            🎯 O que este sistema faz?
          </Typography>
          <Typography paragraph>
            Este é um sistema avançado de auditoria fiscal que utiliza Inteligência Artificial
            para classificar mercadorias automaticamente, garantindo conformidade com as
            regulamentações de ICMS.
          </Typography>

          <Grid container spacing={2} sx={{ mt: 2 }}>
            <Grid item xs={12} md={4}>
              <Card variant="outlined">
                <CardContent>
                  <BusinessIcon color="primary" sx={{ fontSize: 40 }} />
                  <Typography variant="h6">Gestão de Empresas</Typography>
                  <Typography variant="body2">
                    Cadastre e gerencie empresas com todas as informações necessárias
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={4}>
              <Card variant="outlined">
                <CardContent>
                  <AIIcon color="primary" sx={{ fontSize: 40 }} />
                  <Typography variant="h6">IA Avançada</Typography>
                  <Typography variant="body2">
                    8 modelos de IA especializados em classificação NCM e CEST
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={4}>
              <Card variant="outlined">
                <CardContent>
                  <ReportIcon color="primary" sx={{ fontSize: 40 }} />
                  <Typography variant="h6">Relatórios</Typography>
                  <Typography variant="body2">
                    Relatórios executivos completos e auditoria detalhada
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Box>
      ),
    },
    {
      id: 1,
      title: "Cadastro de Empresa",
      description: "Aprenda a cadastrar uma nova empresa no sistema",
      content: (
        <Box>
          <Typography variant="h6" gutterBottom>
            📋 Como cadastrar uma empresa
          </Typography>

          <Alert severity="info" sx={{ mb: 2 }}>
            O cadastro de empresa é o primeiro passo para usar o sistema
          </Alert>

          <List>
            <ListItem>
              <ListItemIcon><CheckIcon /></ListItemIcon>
              <ListItemText
                primary="Dados Básicos"
                secondary="CNPJ, Razão Social, Nome Fantasia"
              />
            </ListItem>
            <ListItem>
              <ListItemIcon><CheckIcon /></ListItemIcon>
              <ListItemText
                primary="Endereço"
                secondary="Endereço completo com busca automática por CEP"
              />
            </ListItem>
            <ListItem>
              <ListItemIcon><CheckIcon /></ListItemIcon>
              <ListItemText
                primary="Contato"
                secondary="Telefone, email e responsável"
              />
            </ListItem>
            <ListItem>
              <ListItemIcon><CheckIcon /></ListItemIcon>
              <ListItemText
                primary="Atividades"
                secondary="CNAEs principal e secundários"
              />
            </ListItem>
          </List>

          <Button
            variant="contained"
            onClick={() => startDemo('empresa')}
            sx={{ mt: 2 }}
          >
            <PlayIcon sx={{ mr: 1 }} />
            Ver Demo de Cadastro
          </Button>
        </Box>
      ),
    },
    {
      id: 2,
      title: "Importação de Dados",
      description: "Como importar dados de produtos para classificação",
      content: (
        <Box>
          <Typography variant="h6" gutterBottom>
            📤 Importação de Produtos
          </Typography>

          <Typography paragraph>
            O sistema suporta importação de dados de diversas fontes:
          </Typography>

          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Card variant="outlined">
                <CardContent>
                  <UploadIcon color="primary" />
                  <Typography variant="h6">Arquivos Excel/CSV</Typography>
                  <Typography variant="body2">
                    Importe planilhas com dados de produtos
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={6}>
              <Card variant="outlined">
                <CardContent>
                  <SettingsIcon color="primary" />
                  <Typography variant="h6">Banco de Dados</Typography>
                  <Typography variant="body2">
                    Conecte diretamente a bancos PostgreSQL/SQL Server
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          <Alert severity="success" sx={{ mt: 2 }}>
            <strong>Campos Obrigatórios:</strong> produto_id, descricao_produto,
            codigo_produto (opcional: codigo_barra, ncm, cest)
          </Alert>

          <Button
            variant="contained"
            onClick={() => startDemo('importacao')}
            sx={{ mt: 2 }}
          >
            <PlayIcon sx={{ mr: 1 }} />
            Ver Demo de Importação
          </Button>
        </Box>
      ),
    },
    {
      id: 3,
      title: "Sistema de Classificação IA",
      description: "Entenda como funciona a classificação automática",
      content: (
        <Box>
          <Typography variant="h6" gutterBottom>
            🤖 Sistema Multi-Agentes de IA
          </Typography>

          <Typography paragraph>
            O sistema utiliza 6 agentes especializados para classificação precisa:
          </Typography>

          <List>
            <ListItem>
              <ListItemIcon><Chip label="1" color="primary" /></ListItemIcon>
              <ListItemText
                primary="Expansion Agent"
                secondary="Enriquece descrições de produtos"
              />
            </ListItem>
            <ListItem>
              <ListItemIcon><Chip label="2" color="primary" /></ListItemIcon>
              <ListItemText
                primary="Aggregation Agent"
                secondary="Agrupa produtos similares"
              />
            </ListItem>
            <ListItem>
              <ListItemIcon><Chip label="3" color="primary" /></ListItemIcon>
              <ListItemText
                primary="NCM Agent"
                secondary="Classifica código NCM"
              />
            </ListItem>
            <ListItem>
              <ListItemIcon><Chip label="4" color="primary" /></ListItemIcon>
              <ListItemText
                primary="CEST Agent"
                secondary="Determina código CEST"
              />
            </ListItem>
            <ListItem>
              <ListItemIcon><Chip label="5" color="primary" /></ListItemIcon>
              <ListItemText
                primary="Reconciler Agent"
                secondary="Valida e resolve conflitos"
              />
            </ListItem>
            <ListItem>
              <ListItemIcon><Chip label="6" color="primary" /></ListItemIcon>
              <ListItemText
                primary="Manager Agent"
                secondary="Coordena todo o processo"
              />
            </ListItem>
          </List>

          <Button
            variant="contained"
            onClick={() => startDemo('classificacao')}
            sx={{ mt: 2 }}
          >
            <PlayIcon sx={{ mr: 1 }} />
            Ver Demo de Classificação
          </Button>
        </Box>
      ),
    },
    {
      id: 4,
      title: "Golden Set",
      description: "Sistema de validação e melhoria contínua",
      content: (
        <Box>
          <Typography variant="h6" gutterBottom>
            🏆 Golden Set - Base de Conhecimento
          </Typography>

          <Typography paragraph>
            O Golden Set é sua base de classificações validadas e corretas:
          </Typography>

          <Alert severity="info" sx={{ mb: 2 }}>
            Cada classificação confirmada enriquece o sistema, melhorando a precisão futura
          </Alert>

          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Card variant="outlined">
                <CardContent>
                  <CheckIcon color="success" />
                  <Typography variant="h6">Validação</Typography>
                  <Typography variant="body2">
                    Revise e confirme classificações da IA
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={6}>
              <Card variant="outlined">
                <CardContent>
                  <SchoolIcon color="primary" />
                  <Typography variant="h6">Aprendizado</Typography>
                  <Typography variant="body2">
                    Sistema aprende com suas correções
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          <Button
            variant="contained"
            onClick={() => startDemo('golden')}
            sx={{ mt: 2 }}
          >
            <PlayIcon sx={{ mr: 1 }} />
            Ver Demo Golden Set
          </Button>
        </Box>
      ),
    },
    {
      id: 5,
      title: "Relatórios e Auditoria",
      description: "Gere relatórios completos e acompanhe auditorias",
      content: (
        <Box>
          <Typography variant="h6" gutterBottom>
            📊 Relatórios Executivos
          </Typography>

          <Typography paragraph>
            Acompanhe todo o processo de classificação com relatórios detalhados:
          </Typography>

          <List>
            <ListItem>
              <ListItemIcon><ReportIcon color="primary" /></ListItemIcon>
              <ListItemText
                primary="Relatório de Classificações"
                secondary="Status e resultados por produto"
              />
            </ListItem>
            <ListItem>
              <ListItemIcon><InfoIcon color="info" /></ListItemIcon>
              <ListItemText
                primary="Auditoria Completa"
                secondary="Logs detalhados de cada decisão"
              />
            </ListItem>
            <ListItem>
              <ListItemIcon><CheckIcon color="success" /></ListItemIcon>
              <ListItemText
                primary="Estatísticas"
                secondary="Métricas de performance e precisão"
              />
            </ListItem>
          </List>

          <Alert severity="success" sx={{ mt: 2 }}>
            <strong>Rastreabilidade Total:</strong> Cada decisão é documentada com
            justificativas, fontes RAG e metadados completos
          </Alert>

          <Button
            variant="contained"
            onClick={() => startDemo('relatorios')}
            sx={{ mt: 2 }}
          >
            <PlayIcon sx={{ mr: 1 }} />
            Ver Demo de Relatórios
          </Button>
        </Box>
      ),
    },
  ];

  return (
    <Box sx={{ maxWidth: 800, margin: 'auto', p: 3 }}>
      <Paper sx={{ p: 3 }}>
        <Typography variant="h4" gutterBottom align="center">
          🎓 Tutorial do Sistema
        </Typography>

        <Typography variant="subtitle1" align="center" sx={{ mb: 3 }}>
          Aprenda a usar todas as funcionalidades em poucos passos
        </Typography>

        <Box sx={{ mb: 3 }}>
          <Typography variant="body2" sx={{ mb: 1 }}>
            Progresso: {Math.round(progress)}%
          </Typography>
          <LinearProgress
            variant="determinate"
            value={progress}
            sx={{ height: 8, borderRadius: 4 }}
          />
        </Box>

        <Stepper activeStep={activeStep} orientation="vertical">
          {steps.map((step, index) => (
            <Step key={step.id} completed={completedSteps.includes(index)}>
              <StepLabel>
                <Typography variant="h6">{step.title}</Typography>
                <Typography variant="body2" color="text.secondary">
                  {step.description}
                </Typography>
              </StepLabel>
              <StepContent>
                <Box sx={{ mt: 2, mb: 1 }}>
                  {step.content}
                </Box>
                <Box sx={{ mb: 2 }}>
                  <div>
                    <Button
                      variant="contained"
                      onClick={handleNext}
                      sx={{ mt: 1, mr: 1 }}
                    >
                      {index === steps.length - 1 ? 'Finalizar Tutorial' : 'Próximo'}
                    </Button>
                    <Button
                      disabled={index === 0}
                      onClick={handleBack}
                      sx={{ mt: 1, mr: 1 }}
                    >
                      Voltar
                    </Button>
                  </div>
                </Box>
              </StepContent>
            </Step>
          ))}
        </Stepper>

        {activeStep === steps.length && (
          <Paper square elevation={0} sx={{ p: 3, mt: 3, textAlign: 'center' }}>
            <Typography variant="h5" gutterBottom>
              🎉 Tutorial Concluído!
            </Typography>
            <Typography variant="body1" sx={{ mb: 3 }}>
              Agora você está pronto para usar todas as funcionalidades do sistema.
            </Typography>
            <Button
              variant="contained"
              size="large"
              onClick={() => window.location.href = '/'}
            >
              Ir para o Sistema
            </Button>
          </Paper>
        )}
      </Paper>

      {/* Dialog para demos */}
      <Dialog
        open={showDemo}
        onClose={() => setShowDemo(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          🎬 Demo: {demoType}
        </DialogTitle>
        <DialogContent>
          <Typography>
            Aqui seria exibida uma demonstração interativa da funcionalidade {demoType}.
            Em uma implementação completa, isso incluiria:
          </Typography>
          <List>
            <ListItem>• Screenshots anotados</ListItem>
            <ListItem>• Vídeos tutoriais</ListItem>
            <ListItem>• Tours interativos</ListItem>
            <ListItem>• Simulações passo-a-passo</ListItem>
          </List>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowDemo(false)}>Fechar</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default OnboardingPage;
