import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline, Box } from '@mui/material';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { ptBR } from 'date-fns/locale';
import { SnackbarProvider } from 'notistack';

import AppHeader from './components/AppHeader';
import Dashboard from './pages/Dashboard';
import RelatoriosPage from './pages/RelatoriosPage';
import ImportPage from './pages/ImportPage';
import AgentsPage from './pages/AgentsPage';
import LoginPage from './pages/LoginPage';
import EmpresasPage from './pages/EmpresasPage';
import CadastroEmpresaPage from './pages/CadastroEmpresaPage';
import ClassificacaoPage from './pages/ClassificacaoPage';
import GoldenSetPage from './pages/GoldenSetPage';
import ImportacaoPage from './pages/ImportacaoPage';
import OnboardingPage from './pages/OnboardingPage';
import { useAuth } from './hooks/useAuth';

// Configuração do tema Material-UI
const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
    background: {
      default: '#f5f5f5',
    },
  },
  typography: {
    fontFamily: 'Roboto, Arial, sans-serif',
    h4: {
      fontWeight: 600,
    },
    h6: {
      fontWeight: 600,
    },
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          borderRadius: 8,
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          borderRadius: 8,
        },
      },
    },
  },
});

// Configuração do React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      staleTime: 5 * 60 * 1000, // 5 minutos
    },
  },
});

// Componente para rotas protegidas
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated } = useAuth();
  
  // Permitir acesso direto à rota /agents para demonstração
  const currentPath = window.location.pathname;
  if (currentPath === '/agents') {
    return <>{children}</>;
  }
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  
  return <>{children}</>;
};

// Layout principal da aplicação
const AppLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <AppHeader />
      <Box component="main" sx={{ flexGrow: 1, py: 3, backgroundColor: 'background.default' }}>
        {children}
      </Box>
    </Box>
  );
};

// Componente principal da aplicação
const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <LocalizationProvider dateAdapter={AdapterDateFns} adapterLocale={ptBR}>
          <CssBaseline />
          <Router>
            <Routes>
              {/* Rota de login */}
              <Route path="/login" element={<LoginPage />} />
              
              {/* Rotas protegidas */}
              <Route
                path="/"
                element={
                  <ProtectedRoute>
                    <AppLayout>
                      <Dashboard />
                    </AppLayout>
                  </ProtectedRoute>
                }
              />
              
              <Route
                path="/relatorios"
                element={
                  <ProtectedRoute>
                    <AppLayout>
                      <RelatoriosPage />
                    </AppLayout>
                  </ProtectedRoute>
                }
              />
              
              <Route
                path="/agents"
                element={
                  <ProtectedRoute>
                    <AppLayout>
                      <AgentsPage />
                    </AppLayout>
                  </ProtectedRoute>
                }
              />
              
              <Route
                path="/import"
                element={
                  <ProtectedRoute>
                    <AppLayout>
                      <ImportPage />
                    </AppLayout>
                  </ProtectedRoute>
                }
              />
              
              <Route
                path="/empresas"
                element={
                  <ProtectedRoute>
                    <AppLayout>
                      <EmpresasPage />
                    </AppLayout>
                  </ProtectedRoute>
                }
              />
              
              <Route
                path="/empresas/cadastrar"
                element={
                  <ProtectedRoute>
                    <AppLayout>
                      <CadastroEmpresaPage />
                    </AppLayout>
                  </ProtectedRoute>
                }
              />
              
              <Route
                path="/empresas/editar/:id"
                element={
                  <ProtectedRoute>
                    <AppLayout>
                      <CadastroEmpresaPage />
                    </AppLayout>
                  </ProtectedRoute>
                }
              />
              
              <Route
                path="/classificacao"
                element={
                  <ProtectedRoute>
                    <AppLayout>
                      <ClassificacaoPage />
                    </AppLayout>
                  </ProtectedRoute>
                }
              />
              
              <Route
                path="/golden-set"
                element={
                  <ProtectedRoute>
                    <AppLayout>
                      <GoldenSetPage />
                    </AppLayout>
                  </ProtectedRoute>
                }
              />
              
              <Route
                path="/importacao"
                element={
                  <ProtectedRoute>
                    <AppLayout>
                      <ImportacaoPage />
                    </AppLayout>
                  </ProtectedRoute>
                }
              />
              
              <Route
                path="/tutorial"
                element={
                  <ProtectedRoute>
                    <AppLayout>
                      <OnboardingPage />
                    </AppLayout>
                  </ProtectedRoute>
                }
              />
              
              {/* Redirect para dashboard se rota não encontrada */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </Router>
        </LocalizationProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
};

export default App;
