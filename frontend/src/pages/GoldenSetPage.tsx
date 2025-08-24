import React, { useState, useEffect } from 'react';
import {
  Box, Paper, Typography, Button, TextField,
  Table, TableBody, TableCell, TableContainer,
  TableHead, TableRow, IconButton, Chip,
  Dialog, DialogTitle, DialogContent, DialogActions,
  Grid, Alert
} from '@mui/material';
import { Add, Edit, Delete, Download, Upload } from '@mui/icons-material';

interface GoldenSetItem {
  id: string;
  descricao_produto: string;
  codigo_produto: string;
  ncm: string;
  cest: string;
  confianca: number;
  data_adicao: string;
}

const GoldenSetPage: React.FC = () => {
  const [items, setItems] = useState<GoldenSetItem[]>([]);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingItem, setEditingItem] = useState<GoldenSetItem | null>(null);

  useEffect(() => {
    carregarGoldenSet();
  }, []);

  const carregarGoldenSet = async () => {
    try {
      const response = await fetch('/api/golden-set');
      const data = await response.json();
      setItems(data);
    } catch (error) {
      console.error('Erro ao carregar Golden Set:', error);
    }
  };

  const salvarItem = async (item: Partial<GoldenSetItem>) => {
    try {
      const method = editingItem ? 'PUT' : 'POST';
      const url = editingItem 
        ? `/api/golden-set/${editingItem.id}`
        : '/api/golden-set';
      
      await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(item)
      });
      
      setDialogOpen(false);
      setEditingItem(null);
      carregarGoldenSet();
    } catch (error) {
      console.error('Erro ao salvar item:', error);
    }
  };

  return (
    <Box sx={{ maxWidth: 1400, mx: 'auto', p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h4">
          Golden Set - Base de Conhecimento
        </Typography>
        
        <Box>
          <Button
            variant="outlined"
            startIcon={<Upload />}
            sx={{ mr: 1 }}
          >
            Importar
          </Button>
          <Button
            variant="outlined"
            startIcon={<Download />}
            sx={{ mr: 1 }}
          >
            Exportar
          </Button>
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={() => setDialogOpen(true)}
          >
            Adicionar
          </Button>
        </Box>
      </Box>

      <Alert severity="info" sx={{ mb: 3 }}>
        O Golden Set é a base de conhecimento de produtos com classificações validadas.
        Use-o para treinar e melhorar a precisão do sistema de classificação automática.
      </Alert>

      <Paper>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Produto</TableCell>
                <TableCell>Código</TableCell>
                <TableCell>NCM</TableCell>
                <TableCell>CEST</TableCell>
                <TableCell>Confiança</TableCell>
                <TableCell>Data</TableCell>
                <TableCell>Ações</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {items.map((item) => (
                <TableRow key={item.id}>
                  <TableCell>{item.descricao_produto}</TableCell>
                  <TableCell>{item.codigo_produto}</TableCell>
                  <TableCell>
                    <Chip label={item.ncm} size="small" />
                  </TableCell>
                  <TableCell>
                    <Chip 
                      label={item.cest || 'N/A'} 
                      size="small" 
                      variant="outlined" 
                    />
                  </TableCell>
                  <TableCell>
                    <Chip 
                      label={`${(item.confianca * 100).toFixed(0)}%`}
                      color={item.confianca > 0.9 ? 'success' : 'warning'}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>{item.data_adicao}</TableCell>
                  <TableCell>
                    <IconButton
                      size="small"
                      onClick={() => {
                        setEditingItem(item);
                        setDialogOpen(true);
                      }}
                    >
                      <Edit />
                    </IconButton>
                    <IconButton size="small" color="error">
                      <Delete />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>

      {/* Dialog para adicionar/editar */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          {editingItem ? 'Editar Item' : 'Adicionar ao Golden Set'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Descrição do Produto"
                multiline
                rows={2}
              />
            </Grid>
            <Grid item xs={6}>
              <TextField
                fullWidth
                label="Código do Produto"
              />
            </Grid>
            <Grid item xs={3}>
              <TextField
                fullWidth
                label="NCM"
              />
            </Grid>
            <Grid item xs={3}>
              <TextField
                fullWidth
                label="CEST"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>
            Cancelar
          </Button>
          <Button variant="contained" onClick={() => salvarItem({})}>
            Salvar
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default GoldenSetPage;