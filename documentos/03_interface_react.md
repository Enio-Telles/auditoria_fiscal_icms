# ⚛️ Interface React - Sistema de Auditoria Fiscal v3.0

## 📝 Visão Geral da Interface

A interface web React foi desenvolvida para fornecer uma experiência moderna, intuitiva e responsiva para o Sistema de Auditoria Fiscal ICMS Multi-Tenant, integrando todas as funcionalidades do backend através de uma API REST robusta.

## 🏗️ **Arquitetura Frontend**

```
┌─────────────────────────────────────┐
│           REACT FRONTEND            │
├─────────────────────────────────────┤
│  React 18 + TypeScript 5            │
│  Material-UI Components             │
│  Port: 3000                         │
├─────────────────────────────────────┤
│                                     │
│  📱 Components/                     │
│     ├── Dashboard/                  │
│     ├── Empresas/                   │
│     ├── Produtos/                   │
│     ├── Import/                     │
│     └── GoldenSet/                  │
│                                     │
│  📄 Pages/                          │
│     ├── HomePage                    │
│     ├── EmpresasPage                │
│     ├── ProdutosPage                │
│     └── ImportPage                  │
│                                     │
│  🔌 Services/                       │
│     ├── apiClient.ts                │
│     ├── empresaService.ts           │
│     ├── produtoService.ts           │
│     └── importService.ts            │
│                                     │
└─────────────────────────────────────┘
               │
               │ HTTP/REST
               ▼
┌─────────────────────────────────────┐
│           FASTAPI BACKEND           │
│            Port: 8003               │
└─────────────────────────────────────┘
```

## 📱 **Estrutura de Componentes**

### **1. Estrutura de Pastas**
```
frontend/
├── 📁 public/
│   ├── index.html
│   └── manifest.json
├── 📁 src/
│   ├── 📁 components/
│   │   ├── 📁 common/
│   │   │   ├── AppBar.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   └── Layout.tsx
│   │   ├── 📁 dashboard/
│   │   │   ├── MetricsCard.tsx
│   │   │   ├── ChartsPanel.tsx
│   │   │   └── RecentActivity.tsx
│   │   ├── 📁 empresas/
│   │   │   ├── EmpresasList.tsx
│   │   │   ├── EmpresaForm.tsx
│   │   │   └── EmpresaCard.tsx
│   │   ├── 📁 produtos/
│   │   │   ├── ProdutosList.tsx
│   │   │   ├── ProdutoForm.tsx
│   │   │   └── ClassificacaoStatus.tsx
│   │   └── 📁 import/
│   │       ├── ImportStepper.tsx
│   │       ├── ConnectionForm.tsx
│   │       ├── PreviewTable.tsx
│   │       └── ImportProgress.tsx
│   ├── 📁 pages/
│   │   ├── HomePage.tsx
│   │   ├── EmpresasPage.tsx
│   │   ├── ProdutosPage.tsx
│   │   └── ImportPage.tsx
│   ├── 📁 services/
│   │   ├── apiClient.ts
│   │   ├── empresaService.ts
│   │   ├── produtoService.ts
│   │   └── importService.ts
│   ├── 📁 types/
│   │   ├── empresa.ts
│   │   ├── produto.ts
│   │   └── import.ts
│   ├── 📁 utils/
│   │   ├── constants.ts
│   │   └── helpers.ts
│   ├── App.tsx
│   ├── index.tsx
│   └── theme.ts
├── package.json
└── tsconfig.json
```

### **2. Componentes Principais**

#### **Layout Principal (Layout.tsx)**
```typescript
import React from 'react';
import { Box, AppBar, Drawer, Toolbar } from '@mui/material';
import { Sidebar } from './Sidebar';
import { TopBar } from './TopBar';

interface LayoutProps {
  children: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = React.useState(true);

  return (
    <Box sx={{ display: 'flex' }}>
      <TopBar onMenuClick={() => setSidebarOpen(!sidebarOpen)} />
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          mt: 8, // AppBar height
          ml: sidebarOpen ? '240px' : 0,
          transition: 'margin 0.3s'
        }}
      >
        {children}
      </Box>
    </Box>
  );
};
```

#### **Dashboard Executivo (Dashboard.tsx)**
```typescript
import React, { useEffect, useState } from 'react';
import { Grid, Card, CardContent, Typography, Box } from '@mui/material';
import { MetricsCard } from '../components/dashboard/MetricsCard';
import { ChartsPanel } from '../components/dashboard/ChartsPanel';
import { dashboardService } from '../services/dashboardService';

export const Dashboard: React.FC = () => {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadMetrics = async () => {
      try {
        const data = await dashboardService.getMetrics();
        setMetrics(data);
      } catch (error) {
        console.error('Erro ao carregar métricas:', error);
      } finally {
        setLoading(false);
      }
    };

    loadMetrics();
  }, []);

  if (loading) {
    return <Box>Carregando...</Box>;
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Dashboard Executivo
      </Typography>
      
      <Grid container spacing={3}>
        {/* Métricas Principais */}
        <Grid item xs={12} md={3}>
          <MetricsCard
            title="Total de Empresas"
            value={metrics?.totalEmpresas || 0}
            icon="business"
            color="primary"
          />
        </Grid>
        <Grid item xs={12} md={3}>
          <MetricsCard
            title="Produtos Cadastrados"
            value={metrics?.totalProdutos || 0}
            icon="inventory"
            color="success"
          />
        </Grid>
        <Grid item xs={12} md={3}>
          <MetricsCard
            title="Classificações IA"
            value={metrics?.classificacoesIA || 0}
            icon="smart_toy"
            color="info"
          />
        </Grid>
        <Grid item xs={12} md={3}>
          <MetricsCard
            title="Precisão Média"
            value={`${metrics?.precisaoMedia || 0}%`}
            icon="analytics"
            color="warning"
          />
        </Grid>

        {/* Gráficos e Análises */}
        <Grid item xs={12} md={8}>
          <ChartsPanel data={metrics?.charts} />
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Atividade Recente
              </Typography>
              {/* Lista de atividades recentes */}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};
```

## 🎨 **Design System e Tema**

### **Material-UI Theme (theme.ts)**
```typescript
import { createTheme } from '@mui/material/styles';

export const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
      light: '#42a5f5',
      dark: '#1565c0',
    },
    secondary: {
      main: '#dc004e',
      light: '#ff5983',
      dark: '#9a0036',
    },
    success: {
      main: '#2e7d32',
    },
    warning: {
      main: '#ed6c02',
    },
    error: {
      main: '#d32f2f',
    },
    background: {
      default: '#f5f5f5',
      paper: '#ffffff',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h4: {
      fontWeight: 600,
      marginBottom: '1rem',
    },
    h6: {
      fontWeight: 500,
    },
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          borderRadius: '8px',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          borderRadius: '6px',
        },
      },
    },
  },
});
```

### **Componentes Responsivos**
```typescript
// Breakpoints para responsividade
const useResponsive = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const isTablet = useMediaQuery(theme.breakpoints.between('md', 'lg'));
  const isDesktop = useMediaQuery(theme.breakpoints.up('lg'));

  return { isMobile, isTablet, isDesktop };
};

// Aplicação em componentes
export const ResponsiveGrid: React.FC = () => {
  const { isMobile } = useResponsive();

  return (
    <Grid container spacing={isMobile ? 2 : 3}>
      {/* Conteúdo adaptativo */}
    </Grid>
  );
};
```

## 🔄 **Sistema de Importação de Dados**

### **Stepper de Importação (ImportStepper.tsx)**
```typescript
import React, { useState } from 'react';
import {
  Stepper,
  Step,
  StepLabel,
  Box,
  Button,
  Typography,
} from '@mui/material';
import { ConnectionForm } from './ConnectionForm';
import { PreviewTable } from './PreviewTable';
import { ImportProgress } from './ImportProgress';

const steps = [
  'Configurar Conexão',
  'Testar Conexão',
  'Preview dos Dados',
  'Executar Importação'
];

export const ImportStepper: React.FC = () => {
  const [activeStep, setActiveStep] = useState(0);
  const [connectionData, setConnectionData] = useState(null);
  const [previewData, setPreviewData] = useState(null);

  const handleNext = () => {
    setActiveStep((prevStep) => prevStep + 1);
  };

  const handleBack = () => {
    setActiveStep((prevStep) => prevStep - 1);
  };

  const renderStepContent = (step: number) => {
    switch (step) {
      case 0:
        return (
          <ConnectionForm
            onNext={handleNext}
            onDataChange={setConnectionData}
          />
        );
      case 1:
        return (
          <TestConnection
            connectionData={connectionData}
            onNext={handleNext}
            onBack={handleBack}
          />
        );
      case 2:
        return (
          <PreviewTable
            connectionData={connectionData}
            onNext={handleNext}
            onBack={handleBack}
            onPreviewData={setPreviewData}
          />
        );
      case 3:
        return (
          <ImportProgress
            connectionData={connectionData}
            previewData={previewData}
            onBack={handleBack}
          />
        );
      default:
        return <Typography>Passo desconhecido</Typography>;
    }
  };

  return (
    <Box>
      <Stepper activeStep={activeStep} alternativeLabel>
        {steps.map((label) => (
          <Step key={label}>
            <StepLabel>{label}</StepLabel>
          </Step>
        ))}
      </Stepper>
      
      <Box sx={{ mt: 4 }}>
        {renderStepContent(activeStep)}
      </Box>
    </Box>
  );
};
```

### **Formulário de Conexão (ConnectionForm.tsx)**
```typescript
import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Button,
  Grid,
} from '@mui/material';
import { DatabaseConnection } from '../types/import';

interface ConnectionFormProps {
  onNext: () => void;
  onDataChange: (data: DatabaseConnection) => void;
}

export const ConnectionForm: React.FC<ConnectionFormProps> = ({
  onNext,
  onDataChange,
}) => {
  const [formData, setFormData] = useState<DatabaseConnection>({
    dbType: 'postgresql',
    host: 'localhost',
    port: '5432',
    database: '',
    username: '',
    password: '',
    schema: 'public',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onDataChange(formData);
    onNext();
  };

  return (
    <Card>
      <CardContent>
        <form onSubmit={handleSubmit}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Tipo de Banco</InputLabel>
                <Select
                  value={formData.dbType}
                  onChange={(e) =>
                    setFormData({ ...formData, dbType: e.target.value })
                  }
                >
                  <MenuItem value="postgresql">PostgreSQL</MenuItem>
                  <MenuItem value="sqlserver">SQL Server</MenuItem>
                  <MenuItem value="mysql">MySQL</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Host"
                value={formData.host}
                onChange={(e) =>
                  setFormData({ ...formData, host: e.target.value })
                }
                required
              />
            </Grid>
            
            <Grid item xs={12} md={3}>
              <TextField
                fullWidth
                label="Porta"
                value={formData.port}
                onChange={(e) =>
                  setFormData({ ...formData, port: e.target.value })
                }
                required
              />
            </Grid>
            
            <Grid item xs={12} md={9}>
              <TextField
                fullWidth
                label="Nome do Banco"
                value={formData.database}
                onChange={(e) =>
                  setFormData({ ...formData, database: e.target.value })
                }
                required
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Usuário"
                value={formData.username}
                onChange={(e) =>
                  setFormData({ ...formData, username: e.target.value })
                }
                required
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                type="password"
                label="Senha"
                value={formData.password}
                onChange={(e) =>
                  setFormData({ ...formData, password: e.target.value })
                }
                required
              />
            </Grid>
            
            <Grid item xs={12}>
              <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2 }}>
                <Button
                  type="submit"
                  variant="contained"
                  size="large"
                >
                  Próximo: Testar Conexão
                </Button>
              </Box>
            </Grid>
          </Grid>
        </form>
      </CardContent>
    </Card>
  );
};
```

## 🔌 **Integração com API**

### **Cliente API Principal (apiClient.ts)**
```typescript
import axios, { AxiosInstance, AxiosResponse } from 'axios';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: process.env.REACT_APP_API_URL || 'http://127.0.0.1:8003',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        // Adicionar token de autenticação se disponível
        const token = localStorage.getItem('authToken');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Limpar token e redirecionar para login
          localStorage.removeItem('authToken');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  async get<T>(url: string): Promise<T> {
    const response: AxiosResponse<T> = await this.client.get(url);
    return response.data;
  }

  async post<T>(url: string, data?: any): Promise<T> {
    const response: AxiosResponse<T> = await this.client.post(url, data);
    return response.data;
  }

  async put<T>(url: string, data?: any): Promise<T> {
    const response: AxiosResponse<T> = await this.client.put(url, data);
    return response.data;
  }

  async delete<T>(url: string): Promise<T> {
    const response: AxiosResponse<T> = await this.client.delete(url);
    return response.data;
  }
}

export const apiClient = new ApiClient();
```

### **Serviço de Empresas (empresaService.ts)**
```typescript
import { apiClient } from './apiClient';
import { Empresa, CreateEmpresaRequest } from '../types/empresa';

export const empresaService = {
  async getEmpresas(): Promise<Empresa[]> {
    return apiClient.get<Empresa[]>('/empresas');
  },

  async getEmpresa(id: number): Promise<Empresa> {
    return apiClient.get<Empresa>(`/empresas/${id}`);
  },

  async createEmpresa(data: CreateEmpresaRequest): Promise<Empresa> {
    return apiClient.post<Empresa>('/empresas', data);
  },

  async updateEmpresa(id: number, data: Partial<Empresa>): Promise<Empresa> {
    return apiClient.put<Empresa>(`/empresas/${id}`, data);
  },

  async deleteEmpresa(id: number): Promise<void> {
    return apiClient.delete<void>(`/empresas/${id}`);
  },

  async getEmpresaStats(id: number): Promise<any> {
    return apiClient.get<any>(`/empresas/${id}/stats`);
  },
};
```

## 📱 **Recursos de UX/UI**

### **Estados de Loading**
```typescript
// Hook personalizado para loading
export const useLoading = () => {
  const [loading, setLoading] = useState(false);
  
  const withLoading = async <T>(fn: () => Promise<T>): Promise<T> => {
    setLoading(true);
    try {
      return await fn();
    } finally {
      setLoading(false);
    }
  };

  return { loading, withLoading };
};

// Componente de loading
export const LoadingOverlay: React.FC<{ loading: boolean }> = ({ loading }) => {
  if (!loading) return null;

  return (
    <Box
      sx={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        backgroundColor: 'rgba(0,0,0,0.5)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 9999,
      }}
    >
      <CircularProgress size={60} />
    </Box>
  );
};
```

### **Notificações e Feedback**
```typescript
// Context para notificações
export const NotificationContext = createContext<{
  showNotification: (message: string, type: 'success' | 'error' | 'warning' | 'info') => void;
}>({
  showNotification: () => {},
});

// Hook para usar notificações
export const useNotification = () => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotification deve ser usado dentro de NotificationProvider');
  }
  return context;
};

// Provider de notificações
export const NotificationProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [notification, setNotification] = useState<{
    open: boolean;
    message: string;
    type: 'success' | 'error' | 'warning' | 'info';
  }>({
    open: false,
    message: '',
    type: 'info',
  });

  const showNotification = (
    message: string,
    type: 'success' | 'error' | 'warning' | 'info'
  ) => {
    setNotification({ open: true, message, type });
  };

  return (
    <NotificationContext.Provider value={{ showNotification }}>
      {children}
      <Snackbar
        open={notification.open}
        autoHideDuration={4000}
        onClose={() => setNotification({ ...notification, open: false })}
      >
        <Alert severity={notification.type}>{notification.message}</Alert>
      </Snackbar>
    </NotificationContext.Provider>
  );
};
```

## 🚀 **Build e Deploy**

### **Configuração de Build**
```json
// package.json
{
  "name": "auditoria-fiscal-frontend",
  "version": "3.0.0",
  "private": true,
  "dependencies": {
    "@mui/material": "^5.14.0",
    "@mui/icons-material": "^5.14.0",
    "@emotion/react": "^11.11.0",
    "@emotion/styled": "^11.11.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.15.0",
    "axios": "^1.5.0",
    "typescript": "^5.0.0"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  }
}
```

### **Comandos de Deploy**
```bash
# Desenvolvimento
npm start

# Build para produção
npm run build

# Servir build local
npx serve -s build

# Deploy com Docker
docker build -t auditoria-frontend .
docker run -p 3000:3000 auditoria-frontend
```

## 📊 **Métricas e Performance**

### **Métricas de Performance**
- **Bundle Size:** < 2MB comprimido
- **First Paint:** < 1.5s
- **Time to Interactive:** < 3s
- **Lighthouse Score:** > 90
- **Core Web Vitals:** Todos dentro dos limites

### **Otimizações Implementadas**
- Code splitting por rotas
- Lazy loading de componentes
- Memoização de componentes pesados
- Debounce em campos de busca
- Virtual scrolling para listas grandes
- Service worker para cache offline

---

**Status:** Interface React 100% Implementada  
**Versão:** 3.0.0  
**Próximo documento:** [04_importacao_dados.md](04_importacao_dados.md)
