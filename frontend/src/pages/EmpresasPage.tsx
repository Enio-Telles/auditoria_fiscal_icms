import React, { useState } from 'react';
import {
  Container,
  Typography,
  Box,
  Button,
  TextField,
  Paper,
  Grid,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Card,
  CardContent,
  CardActions,
  Chip,
  InputAdornment,
} from '@mui/material';
import {
  Add,
  Search,
  Edit,
  Delete,
  Business,
  Phone,
  Email,
  LocationOn,
} from '@mui/icons-material';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import { useForm } from 'react-hook-form';
import { useEmpresas, useCreateEmpresa, useUpdateEmpresa, useDeleteEmpresa } from '../hooks/useEmpresas';
import { Empresa, EmpresaForm } from '../types';

const EmpresasPage: React.FC = () => {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [openDialog, setOpenDialog] = useState(false);
  const [editingEmpresa, setEditingEmpresa] = useState<Empresa | null>(null);

  const { data: empresasData, isLoading } = useEmpresas(page, 10, search);
  const createEmpresaMutation = useCreateEmpresa();
  const updateEmpresaMutation = useUpdateEmpresa();
  const deleteEmpresaMutation = useDeleteEmpresa();

  const { register, handleSubmit, reset, formState: { errors } } = useForm<EmpresaForm>();

  const handleOpenDialog = (empresa?: Empresa) => {
    if (empresa) {
      setEditingEmpresa(empresa);
      reset({
        cnpj: empresa.cnpj,
        razao_social: empresa.razao_social,
        nome_fantasia: empresa.nome_fantasia || '',
        atividade_principal: empresa.atividade_principal || '',
        regime_tributario: empresa.regime_tributario || '',
      });
    } else {
      setEditingEmpresa(null);
      reset();
    }
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setEditingEmpresa(null);
    reset();
  };

  const onSubmit = (data: EmpresaForm) => {
    if (editingEmpresa) {
      updateEmpresaMutation.mutate({
        id: editingEmpresa.id,
        empresa: data,
      });
    } else {
      createEmpresaMutation.mutate(data);
    }
    handleCloseDialog();
  };

  const handleDelete = (id: number) => {
    if (window.confirm('Tem certeza que deseja excluir esta empresa?')) {
      deleteEmpresaMutation.mutate(id);
    }
  };

  const columns: GridColDef[] = [
    {
      field: 'cnpj',
      headerName: 'CNPJ',
      width: 150,
      renderCell: (params) => {
        const cnpj = params.value;
        return cnpj ? `${cnpj.slice(0, 2)}.${cnpj.slice(2, 5)}.${cnpj.slice(5, 8)}/${cnpj.slice(8, 12)}-${cnpj.slice(12)}` : '';
      },
    },
    { field: 'razao_social', headerName: 'Razão Social', width: 300 },
    { field: 'nome_fantasia', headerName: 'Nome Fantasia', width: 200 },
    { field: 'atividade_principal', headerName: 'Atividade', width: 250 },
    {
      field: 'regime_tributario',
      headerName: 'Regime',
      width: 150,
      renderCell: (params) => (
        <Chip
          label={params.value}
          size="small"
          color={params.value === 'Simples Nacional' ? 'success' : 'primary'}
        />
      ),
    },
    {
      field: 'ativo',
      headerName: 'Status',
      width: 100,
      renderCell: (params) => (
        <Chip
          label={params.value ? 'Ativo' : 'Inativo'}
          size="small"
          color={params.value ? 'success' : 'error'}
        />
      ),
    },
    {
      field: 'actions',
      headerName: 'Ações',
      width: 120,
      renderCell: (params) => (
        <Box>
          <IconButton
            size="small"
            onClick={() => handleOpenDialog(params.row)}
          >
            <Edit />
          </IconButton>
          <IconButton
            size="small"
            onClick={() => handleDelete(params.row.id)}
            color="error"
          >
            <Delete />
          </IconButton>
        </Box>
      ),
    },
  ];

  return (
    <Container maxWidth="xl">
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          Empresas
        </Typography>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={() => handleOpenDialog()}
        >
          Nova Empresa
        </Button>
      </Box>

      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={6}>
          <TextField
            fullWidth
            placeholder="Buscar empresas..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <Search />
                </InputAdornment>
              ),
            }}
          />
        </Grid>
      </Grid>

      <Paper sx={{ height: 600, width: '100%' }}>
        <DataGrid
          rows={empresasData?.items || []}
          columns={columns}
          loading={isLoading}
          pageSizeOptions={[10, 25, 50]}
          disableRowSelectionOnClick
          sx={{
            '& .MuiDataGrid-cell:hover': {
              color: 'primary.main',
            },
          }}
        />
      </Paper>

      {/* Dialog para criar/editar empresa */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogTitle>
            {editingEmpresa ? 'Editar Empresa' : 'Nova Empresa'}
          </DialogTitle>
          <DialogContent>
            <Grid container spacing={2} sx={{ mt: 1 }}>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="CNPJ"
                  {...register('cnpj', {
                    required: 'CNPJ é obrigatório',
                    pattern: {
                      value: /^\d{14}$/,
                      message: 'CNPJ deve ter 14 dígitos',
                    },
                  })}
                  error={!!errors.cnpj}
                  helperText={errors.cnpj?.message}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Regime Tributário"
                  {...register('regime_tributario')}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Razão Social"
                  {...register('razao_social', {
                    required: 'Razão Social é obrigatória',
                  })}
                  error={!!errors.razao_social}
                  helperText={errors.razao_social?.message}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Nome Fantasia"
                  {...register('nome_fantasia')}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Atividade Principal"
                  {...register('atividade_principal')}
                />
              </Grid>
            </Grid>
          </DialogContent>
          <DialogActions>
            <Button onClick={handleCloseDialog}>Cancelar</Button>
            <Button
              type="submit"
              variant="contained"
              disabled={createEmpresaMutation.isPending || updateEmpresaMutation.isPending}
            >
              {editingEmpresa ? 'Atualizar' : 'Criar'}
            </Button>
          </DialogActions>
        </form>
      </Dialog>
    </Container>
  );
};

export default EmpresasPage;
