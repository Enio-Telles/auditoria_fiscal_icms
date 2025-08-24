import React, { useEffect } from 'react';
import {
  Container,
  Paper,
  Box,
  Typography,
  TextField,
  Button,
  Alert,
  Card,
  CardContent,
} from '@mui/material';
import { Lock, Business } from '@mui/icons-material';
import { useForm } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { LoginRequest } from '../types';

const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const { login, isAuthenticated, loginLoading, loginError } = useAuth();

  const { register, handleSubmit, formState: { errors } } = useForm<LoginRequest>();

  // Redirecionar se já autenticado
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/');
    }
  }, [isAuthenticated, navigate]);

  const onSubmit = (data: LoginRequest) => {
    login(data);
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      }}
    >
      <Container maxWidth="sm">
        <Card elevation={8}>
          <CardContent sx={{ p: 4 }}>
            <Box sx={{ textAlign: 'center', mb: 4 }}>
              <Business sx={{ fontSize: 60, color: 'primary.main', mb: 2 }} />
              <Typography variant="h4" component="h1" gutterBottom>
                Auditoria Fiscal ICMS
              </Typography>
              <Typography variant="body1" color="text.secondary">
                Sistema de Classificação Automática NCM/CEST
              </Typography>
            </Box>

            <form onSubmit={handleSubmit(onSubmit)}>
              <Box sx={{ mb: 3 }}>
                <TextField
                  fullWidth
                  label="Usuário"
                  variant="outlined"
                  {...register('username', {
                    required: 'Usuário é obrigatório',
                  })}
                  error={!!errors.username}
                  helperText={errors.username?.message}
                  sx={{ mb: 2 }}
                />

                <TextField
                  fullWidth
                  label="Senha"
                  type="password"
                  variant="outlined"
                  {...register('password', {
                    required: 'Senha é obrigatória',
                  })}
                  error={!!errors.password}
                  helperText={errors.password?.message}
                />
              </Box>

              {loginError && (
                <Alert severity="error" sx={{ mb: 3 }}>
                  Erro no login. Verifique suas credenciais e tente novamente.
                </Alert>
              )}

              <Button
                type="submit"
                fullWidth
                variant="contained"
                size="large"
                disabled={loginLoading}
                startIcon={<Lock />}
                sx={{ mb: 3 }}
              >
                {loginLoading ? 'Entrando...' : 'Entrar'}
              </Button>
            </form>

            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="body2" color="text.secondary">
                Desenvolvido com IA Generativa
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Versão 22.0 - Fase 7
              </Typography>
            </Box>
          </CardContent>
        </Card>
      </Container>
    </Box>
  );
};

export default LoginPage;
