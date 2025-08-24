import React, { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Button,
  Alert,
  AlertTitle,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
  LinearProgress,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  ExpandMore,
  Warning,
  Error,
  CheckCircle,
  Info,
  Gavel,
  Security,
  Assignment,
  Description,
  Download,
  Visibility,
  PictureAsPdf,
  TableChart,
} from '@mui/icons-material';
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  Treemap,
} from 'recharts';

export interface ComplianceData {
  overallScore: number;
  complianceAreas: Array<{
    area: string;
    score: number;
    status: 'compliant' | 'warning' | 'critical';
    issues: number;
    description: string;
    recommendations: string[];
  }>;
  riskAssessment: Array<{
    riskType: string;
    level: 'low' | 'medium' | 'high' | 'critical';
    probability: number;
    impact: number;
    affectedProducts: number;
    description: string;
    mitigationActions: string[];
  }>;
  auditTrail: Array<{
    date: string;
    action: string;
    user: string;
    details: string;
    classification: string;
    impact: 'low' | 'medium' | 'high';
  }>;
  ncmCompliance: Array<{
    ncmCode: string;
    description: string;
    totalProducts: number;
    correctClassifications: number;
    incorrectClassifications: number;
    pendingReview: number;
    complianceRate: number;
  }>;
  regulatoryAlerts: Array<{
    id: string;
    severity: 'info' | 'warning' | 'error';
    title: string;
    description: string;
    affectedNCMs: string[];
    deadline?: string;
    status: 'open' | 'in_progress' | 'resolved';
  }>;
}

interface ComplianceReportProps {
  data: ComplianceData;
  isLoading?: boolean;
  onExportReport?: (format: 'pdf' | 'excel') => void;
}

const ComplianceReport: React.FC<ComplianceReportProps> = ({
  data,
  isLoading = false,
  onExportReport,
}) => {
  const [selectedRisk, setSelectedRisk] = useState<any>(null);
  const [alertDetailsOpen, setAlertDetailsOpen] = useState(false);
  const [selectedAlert, setSelectedAlert] = useState<any>(null);

  const getScoreColor = (score: number) => {
    if (score >= 90) return 'success';
    if (score >= 70) return 'warning';
    return 'error';
  };

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'critical': return '#d32f2f';
      case 'high': return '#f57c00';
      case 'medium': return '#fbc02d';
      case 'low': return '#388e3c';
      default: return '#757575';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'compliant': return <CheckCircle color="success" />;
      case 'warning': return <Warning color="warning" />;
      case 'critical': return <Error color="error" />;
      default: return <Info color="info" />;
    }
  };

  const complianceChartData = data.complianceAreas.map(area => ({
    name: area.area,
    value: area.score,
    color: area.status === 'compliant' ? '#4caf50' : 
           area.status === 'warning' ? '#ff9800' : '#f44336'
  }));

  const riskMatrixData = data.riskAssessment.map(risk => ({
    name: risk.riskType,
    value: risk.probability * risk.impact,
    probability: risk.probability,
    impact: risk.impact,
    level: risk.level,
    affected: risk.affectedProducts,
  }));

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box>
          <Typography variant="h4" fontWeight="bold" gutterBottom>
            Relatório de Conformidade Fiscal
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Análise completa de conformidade e riscos regulatórios
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<PictureAsPdf />}
            onClick={() => onExportReport?.('pdf')}
            color="error"
          >
            PDF
          </Button>
          <Button
            variant="outlined"
            startIcon={<TableChart />}
            onClick={() => onExportReport?.('excel')}
            color="success"
          >
            Excel
          </Button>
        </Box>
      </Box>

      {/* Score Geral de Conformidade */}
      <Card sx={{ mb: 3, background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
        <CardContent sx={{ color: 'white', textAlign: 'center', py: 4 }}>
          <Typography variant="h2" fontWeight="bold" sx={{ mb: 1 }}>
            {data.overallScore.toFixed(1)}%
          </Typography>
          <Typography variant="h5" sx={{ mb: 2 }}>
            Score Geral de Conformidade
          </Typography>
          <LinearProgress
            variant="determinate"
            value={data.overallScore}
            sx={{
              height: 8,
              borderRadius: 4,
              backgroundColor: 'rgba(255,255,255,0.3)',
              '& .MuiLinearProgress-bar': {
                backgroundColor: 'white',
              },
            }}
          />
          <Typography variant="body2" sx={{ mt: 2, opacity: 0.9 }}>
            {data.overallScore >= 90 ? 'Excelente conformidade' :
             data.overallScore >= 70 ? 'Conformidade adequada' : 'Requer atenção imediata'}
          </Typography>
        </CardContent>
      </Card>

      {/* Alertas Regulatórios */}
      {data.regulatoryAlerts.filter(alert => alert.status === 'open').length > 0 && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          <AlertTitle>Alertas Regulatórios Ativos</AlertTitle>
          {data.regulatoryAlerts.filter(alert => alert.status === 'open').length} alertas requerem atenção.
          <Button
            size="small"
            onClick={() => setAlertDetailsOpen(true)}
            sx={{ ml: 2 }}
          >
            Ver Detalhes
          </Button>
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Áreas de Conformidade */}
        <Grid item xs={12} lg={6}>
          <Paper sx={{ p: 3, height: 400 }}>
            <Typography variant="h6" gutterBottom>
              Conformidade por Área
            </Typography>
            <ResponsiveContainer width="100%" height="85%">
              <PieChart>
                <Pie
                  data={complianceChartData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, value }) => `${name}: ${value}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {complianceChartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <RechartsTooltip />
              </PieChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* Matriz de Riscos */}
        <Grid item xs={12} lg={6}>
          <Paper sx={{ p: 3, height: 400 }}>
            <Typography variant="h6" gutterBottom>
              Matriz de Riscos
            </Typography>
            <ResponsiveContainer width="100%" height="85%">
              <Treemap
                data={riskMatrixData}
                dataKey="value"
                stroke="#fff"
                fill="#8884d8"
              />
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* Detalhamento de Áreas de Conformidade */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Detalhamento por Área
            </Typography>
            {data.complianceAreas.map((area, index) => (
              <Accordion key={index}>
                <AccordionSummary
                  expandIcon={<ExpandMore />}
                  sx={{
                    backgroundColor: area.status === 'compliant' ? 'success.light' :
                                     area.status === 'warning' ? 'warning.light' : 'error.light',
                    color: area.status === 'compliant' ? 'success.contrastText' :
                           area.status === 'warning' ? 'warning.contrastText' : 'error.contrastText',
                  }}
                >
                  <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                    {getStatusIcon(area.status)}
                    <Typography sx={{ ml: 2, flexGrow: 1 }}>{area.area}</Typography>
                    <Chip
                      label={`${area.score}%`}
                      color={getScoreColor(area.score)}
                      size="small"
                      sx={{ mr: 2 }}
                    />
                    <Typography variant="body2">
                      {area.issues} {area.issues === 1 ? 'issue' : 'issues'}
                    </Typography>
                  </Box>
                </AccordionSummary>
                <AccordionDetails>
                  <Box>
                    <Typography variant="body2" paragraph>
                      {area.description}
                    </Typography>
                    <Typography variant="subtitle2" gutterBottom>
                      Recomendações:
                    </Typography>
                    <List dense>
                      {area.recommendations.map((rec, idx) => (
                        <ListItem key={idx}>
                          <ListItemIcon>
                            <CheckCircle color="primary" fontSize="small" />
                          </ListItemIcon>
                          <ListItemText primary={rec} />
                        </ListItem>
                      ))}
                    </List>
                  </Box>
                </AccordionDetails>
              </Accordion>
            ))}
          </Paper>
        </Grid>

        {/* Análise de Riscos Detalhada */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Análise de Riscos
            </Typography>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Tipo de Risco</TableCell>
                    <TableCell align="center">Nível</TableCell>
                    <TableCell align="right">Probabilidade</TableCell>
                    <TableCell align="right">Impacto</TableCell>
                    <TableCell align="right">Produtos Afetados</TableCell>
                    <TableCell align="center">Ações</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {data.riskAssessment.map((risk, index) => (
                    <TableRow key={index} hover>
                      <TableCell>
                        <Typography variant="subtitle2">{risk.riskType}</Typography>
                        <Typography variant="caption" color="text.secondary">
                          {risk.description}
                        </Typography>
                      </TableCell>
                      <TableCell align="center">
                        <Chip
                          label={risk.level.toUpperCase()}
                          size="small"
                          sx={{
                            backgroundColor: getRiskColor(risk.level),
                            color: 'white',
                            fontWeight: 'bold',
                          }}
                        />
                      </TableCell>
                      <TableCell align="right">
                        <LinearProgress
                          variant="determinate"
                          value={risk.probability}
                          sx={{ width: 60, mr: 1 }}
                        />
                        {risk.probability}%
                      </TableCell>
                      <TableCell align="right">
                        <LinearProgress
                          variant="determinate"
                          value={risk.impact}
                          color="secondary"
                          sx={{ width: 60, mr: 1 }}
                        />
                        {risk.impact}%
                      </TableCell>
                      <TableCell align="right">
                        {risk.affectedProducts.toLocaleString()}
                      </TableCell>
                      <TableCell align="center">
                        <Tooltip title="Ver detalhes">
                          <IconButton
                            size="small"
                            onClick={() => setSelectedRisk(risk)}
                          >
                            <Visibility />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        </Grid>

        {/* Conformidade NCM */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Conformidade por Código NCM
            </Typography>
            <TableContainer sx={{ maxHeight: 400 }}>
              <Table stickyHeader>
                <TableHead>
                  <TableRow>
                    <TableCell>Código NCM</TableCell>
                    <TableCell>Descrição</TableCell>
                    <TableCell align="right">Total</TableCell>
                    <TableCell align="right">Corretos</TableCell>
                    <TableCell align="right">Incorretos</TableCell>
                    <TableCell align="right">Pendentes</TableCell>
                    <TableCell align="right">Taxa de Conformidade</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {data.ncmCompliance.map((ncm, index) => (
                    <TableRow key={index} hover>
                      <TableCell>
                        <Typography variant="subtitle2" fontFamily="monospace">
                          {ncm.ncmCode}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" noWrap sx={{ maxWidth: 200 }}>
                          {ncm.description}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">{ncm.totalProducts}</TableCell>
                      <TableCell align="right">
                        <Typography color="success.main">
                          {ncm.correctClassifications}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Typography color="error.main">
                          {ncm.incorrectClassifications}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Typography color="warning.main">
                          {ncm.pendingReview}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end' }}>
                          <LinearProgress
                            variant="determinate"
                            value={ncm.complianceRate * 100}
                            color={getScoreColor(ncm.complianceRate * 100)}
                            sx={{ width: 60, mr: 1 }}
                          />
                          <Typography variant="body2">
                            {(ncm.complianceRate * 100).toFixed(1)}%
                          </Typography>
                        </Box>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        </Grid>
      </Grid>

      {/* Dialog para Detalhes de Risco */}
      <Dialog
        open={!!selectedRisk}
        onClose={() => setSelectedRisk(null)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Detalhes do Risco: {selectedRisk?.riskType}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 1 }}>
            <Typography variant="body1" paragraph>
              {selectedRisk?.description}
            </Typography>
            <Divider sx={{ my: 2 }} />
            <Typography variant="subtitle2" gutterBottom>
              Ações de Mitigação:
            </Typography>
            <List>
              {selectedRisk?.mitigationActions.map((action: string, idx: number) => (
                <ListItem key={idx}>
                  <ListItemIcon>
                    <Security color="primary" />
                  </ListItemIcon>
                  <ListItemText primary={action} />
                </ListItem>
              ))}
            </List>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSelectedRisk(null)}>Fechar</Button>
          <Button variant="contained" startIcon={<Assignment />}>
            Criar Plano de Ação
          </Button>
        </DialogActions>
      </Dialog>

      {/* Dialog para Alertas Regulatórios */}
      <Dialog
        open={alertDetailsOpen}
        onClose={() => setAlertDetailsOpen(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>Alertas Regulatórios</DialogTitle>
        <DialogContent>
          <List>
            {data.regulatoryAlerts.map((alert, index) => (
              <React.Fragment key={alert.id}>
                <ListItem alignItems="flex-start">
                  <ListItemIcon>
                    {alert.severity === 'error' ? <Error color="error" /> :
                     alert.severity === 'warning' ? <Warning color="warning" /> :
                     <Info color="info" />}
                  </ListItemIcon>
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Typography variant="subtitle1">{alert.title}</Typography>
                        <Chip
                          label={alert.status.replace('_', ' ').toUpperCase()}
                          size="small"
                          color={alert.status === 'resolved' ? 'success' : 'warning'}
                        />
                      </Box>
                    }
                    secondary={
                      <Box>
                        <Typography variant="body2" paragraph>
                          {alert.description}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          NCMs Afetados: {alert.affectedNCMs.join(', ')}
                        </Typography>
                        {alert.deadline && (
                          <Typography variant="caption" color="error.main" display="block">
                            Prazo: {alert.deadline}
                          </Typography>
                        )}
                      </Box>
                    }
                  />
                </ListItem>
                {index < data.regulatoryAlerts.length - 1 && <Divider />}
              </React.Fragment>
            ))}
          </List>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAlertDetailsOpen(false)}>Fechar</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ComplianceReport;
