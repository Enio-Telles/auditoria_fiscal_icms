import React, { useState } from 'react';
import {
  Box, Paper, Typography, TextField, Button,
  Grid, Card, CardContent, Chip, Alert,
  Table, TableBody, TableCell, TableContainer,
  TableHead, TableRow, LinearProgress
} from '@mui/material';
import { Search, CheckCircle, Cancel, Lightbulb } from '@mui/icons-material';

const ClassificacaoPage: React.FC = () => {
  const [produto, setProduto] = useState('');
  const [classificando, setClassificando] = useState(false);
  const [resultado, setResultado] = useState<any>(null);

  const classificarProduto = async () => {
    if (!produto.trim()) return;

    setClassificando(true);
    try {
      const response = await fetch('/api/classification/classify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          description: produto,
          strategy: 'ensemble'
        })
      });

      const result = await response.json();
      setResultado(result);
    } catch (error) {
      console.error('Erro na classificação:', error);
    } finally {
      setClassificando(false);
    }
  };

  return (
    <Box sx={{ maxWidth: 1200, mx: 'auto', p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Classificação de Produtos
      </Typography>

      <Grid container spacing={3}>
        {/* Formulário de entrada */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Produto para Classificar
            </Typography>

            <TextField
              fullWidth
              multiline
              rows={4}
              label="Descrição do produto"
              value={produto}
              onChange={(e) => setProduto(e.target.value)}
              placeholder="Ex: Smartphone Samsung Galaxy A54 128GB 5G"
              sx={{ mb: 2 }}
            />

            <Button
              variant="contained"
              onClick={classificarProduto}
              disabled={classificando || !produto.trim()}
              startIcon={<Search />}
              fullWidth
              size="large"
            >
              {classificando ? 'Classificando...' : 'Classificar Produto'}
            </Button>

            {classificando && (
              <LinearProgress sx={{ mt: 2 }} />
            )}
          </Paper>
        </Grid>

        {/* Resultado */}
        <Grid item xs={12} md={6}>
          {resultado && (
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Resultado da Classificação
              </Typography>

              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Card>
                    <CardContent>
                      <Typography color="textSecondary" gutterBottom>
                        NCM
                      </Typography>
                      <Typography variant="h5">
                        {resultado.ncm_code}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>

                <Grid item xs={6}>
                  <Card>
                    <CardContent>
                      <Typography color="textSecondary" gutterBottom>
                        CEST
                      </Typography>
                      <Typography variant="h5">
                        {resultado.cest_code || 'N/A'}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>

              <Box sx={{ mt: 2 }}>
                <Chip
                  label={`Confiança: ${(resultado.confidence * 100).toFixed(1)}%`}
                  color={resultado.confidence > 0.8 ? 'success' : 'warning'}
                  sx={{ mr: 1 }}
                />
                <Chip
                  label={resultado.strategy}
                  variant="outlined"
                />
              </Box>

              <Alert severity="info" sx={{ mt: 2 }}>
                <Typography variant="body2">
                  <strong>Justificativa:</strong> {resultado.justification}
                </Typography>
              </Alert>

              <Box sx={{ mt: 2 }}>
                <Button
                  variant="contained"
                  color="success"
                  startIcon={<CheckCircle />}
                  sx={{ mr: 1 }}
                >
                  Aprovar
                </Button>
                <Button
                  variant="outlined"
                  color="error"
                  startIcon={<Cancel />}
                >
                  Rejeitar
                </Button>
              </Box>
            </Paper>
          )}
        </Grid>
      </Grid>
    </Box>
  );
};

export default ClassificacaoPage;
