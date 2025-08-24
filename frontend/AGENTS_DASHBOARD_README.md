# 🖥️ Interface de Agentes - Dashboard

## 🎯 Visão Geral

O Dashboard de Agentes é uma interface React completa para monitoramento e controle do sistema de agentes especializados em classificação fiscal NCM/CEST. Oferece controle em tempo real, métricas de performance e execução de tarefas.

## 🚀 Início Rápido

### 1. **Desenvolvimento com Mock API**
```bash
# Terminal 1: Inicie o servidor mock
cd frontend/src/services/mock
python mock_agents_api.py

# Terminal 2: Inicie o React
cd frontend
npm start

# Acesse: http://localhost:3000/agents
```

### 2. **Produção com API Real**
```bash
# Certifique-se que a API real está rodando
.\start_sistema_completo.bat

# Inicie o React
cd frontend
npm start

# Acesse: http://localhost:3000/agents
```

## 🏗️ Arquitetura

### **Componentes Principais**

```
src/
├── components/agents/
│   ├── AgentCard.tsx           # Card individual de agente
│   ├── SystemMetricsCard.tsx   # Métricas do sistema
│   └── AgentsPage.tsx          # Página principal do dashboard
├── services/
│   ├── agentsService.ts        # Camada de API
│   └── mock/
│       ├── mock_agents_api.py  # Servidor mock Flask
│       └── mock_data.py        # Dados simulados
├── hooks/
│   └── useAgents.ts            # Hook para estado dos agentes
└── types/
    └── agents.ts               # Definições TypeScript
```

### **Fluxo de Dados**

```
React Components → useAgents Hook → agentsService → API Backend
                                                 ↓
                                           PostgreSQL
```

## 🔧 Funcionalidades

### **Dashboard Principal**
- **📊 Visão Geral:** Cards com métricas de cada agente
- **🎛️ Controles:** Start, stop, restart de agentes individuais
- **📈 Métricas do Sistema:** Performance global em tempo real
- **🔄 Auto-refresh:** Atualização automática a cada 30 segundos

### **Aba de Tarefas**
- **📋 Lista de Tarefas:** Histórico completo de execuções
- **▶️ Execução:** Interface para rodar tarefas específicas
- **📊 Status:** Acompanhamento de progresso em tempo real
- **📄 Resultados:** Visualização detalhada dos outputs

### **Aba de Workflows**
- **🔄 Workflows Ativos:** Monitoramento de workflows multi-agente
- **🎯 Orquestração:** Controle de sequências de agentes
- **📈 Performance:** Métricas de workflows complexos

### **Classificação Rápida**
- **⚡ Teste Instantâneo:** Interface para classificar produtos rapidamente
- **🎯 Validação:** Verificação de resultados NCM/CEST
- **🔍 Debug:** Ferramenta para testar agentes específicos

## 🎨 Interface

### **Material-UI Components**
- **Cards:** Display de informações dos agentes
- **Tabs:** Organização por funcionalidade
- **Progress Bars:** Indicadores de performance
- **Dialogs:** Criação e edição de tarefas
- **Snackbar:** Notificações e feedback
- **FAB (Floating Action Button):** Ações rápidas

### **Design Responsivo**
- **Grid Layout:** Adaptação automática a diferentes telas
- **Mobile-First:** Interface otimizada para dispositivos móveis
- **Dark/Light Mode:** Suporte a temas (futuro)

## 🔌 Integração com API

### **Endpoints Utilizados**

```typescript
// Sistema
GET /api/agents/status          // Status geral do sistema
GET /api/agents/metrics         // Métricas em tempo real

// Agentes
GET /api/agents                 // Lista todos os agentes
POST /api/agents/:id/start      // Inicia agente específico
POST /api/agents/:id/stop       // Para agente específico
POST /api/agents/:id/restart    // Reinicia agente específico

// Tarefas
GET /api/tasks                  // Lista tarefas
POST /api/tasks                 // Cria nova tarefa
GET /api/tasks/:id              // Detalhes da tarefa
POST /api/tasks/:id/execute     // Executa tarefa

// Workflows
GET /api/workflows              // Lista workflows
POST /api/workflows             // Cria workflow
POST /api/workflows/:id/execute // Executa workflow

// Classificação Rápida
POST /api/classify/quick        // Classificação instantânea
```

### **Tratamento de Erros**
- **Network Errors:** Retry automático com backoff
- **API Errors:** Exibição de mensagens user-friendly
- **Loading States:** Indicadores visuais durante requests
- **Offline Support:** Cache local para resiliência

## 🧪 Mock API para Desenvolvimento

### **Servidor Flask**
```python
# mock_agents_api.py
# - 20+ endpoints simulados
# - Dados realistas
# - Delay de rede simulado
# - CORS configurado
# - Logs detalhados
```

### **Dados Simulados**
```python
# mock_data.py
# - 5 agentes especializados
# - Métricas históricas
# - Tarefas com diferentes status
# - Workflows complexos
# - Simulação de performance real
```

### **Configuração Mock**
```bash
# Instalar dependências
pip install flask flask-cors

# Rodar servidor mock
cd frontend/src/services/mock
python mock_agents_api.py

# Output esperado:
# * Running on http://127.0.0.1:5001
# * Todos os endpoints disponíveis
# * CORS habilitado
```

## 🔧 Desenvolvimento

### **Estrutura TypeScript**

```typescript
// types/agents.ts
interface Agent {
  id: string;
  name: string;
  type: AgentType;
  status: AgentStatus;
  description: string;
  metrics: AgentMetrics;
  config: AgentConfig;
  health: HealthStatus;
  lastActivity: string;
  uptime: number;
}

interface SystemMetrics {
  totalAgents: number;
  activeAgents: number;
  totalTasks: number;
  completedTasks: number;
  failedTasks: number;
  avgResponseTime: number;
  systemHealth: 'healthy' | 'warning' | 'critical';
  cpuUsage: number;
  memoryUsage: number;
  diskUsage: number;
}
```

### **Custom Hooks**

```typescript
// hooks/useAgents.ts
export const useAgents = () => {
  // React Query para cache e sincronização
  // Auto-refresh a cada 30 segundos
  // Optimistic updates para melhor UX
  // Error handling robusto
  // Loading states granulares
}
```

### **Service Layer**

```typescript
// services/agentsService.ts
class AgentsService {
  // HTTP client configurado
  // Base URL dinâmica (mock/produção)
  // Interceptors para auth
  // Error handling centralizado
  // Retry logic
}
```

## 🧪 Testes

### **Cenários de Teste**
```bash
# 1. Testar com mock API
python frontend/src/services/mock/mock_agents_api.py

# 2. Verificar componentes no React
npm test

# 3. Testar integração completa
# Inicie backend real + frontend
.\start_sistema_completo.bat
cd frontend && npm start
```

### **Casos de Uso**
1. **Monitoramento:** Verificar status de todos os agentes
2. **Controle:** Start/stop de agentes específicos
3. **Execução:** Rodar classificação de produtos
4. **Performance:** Monitorar métricas em tempo real
5. **Debug:** Testar agentes isoladamente

## 🚀 Deploy

### **Build de Produção**
```bash
cd frontend
npm run build

# Output em frontend/build/
# Pronto para deploy em qualquer servidor web
```

### **Configuração de Ambiente**
```typescript
// src/config/env.ts
const config = {
  development: {
    apiUrl: 'http://127.0.0.1:5001',  // Mock API
    mockMode: true
  },
  production: {
    apiUrl: 'http://127.0.0.1:8003',  // API Real
    mockMode: false
  }
}
```

## 📚 Próximas Funcionalidades

### **Planejadas**
- [ ] **🌙 Dark Mode:** Suporte a tema escuro
- [ ] **📱 PWA:** Progressive Web App
- [ ] **🔔 Notificações:** Push notifications
- [ ] **📊 Charts:** Gráficos avançados com Chart.js
- [ ] **🔍 Busca:** Filtros avançados
- [ ] **📤 Export:** Download de relatórios
- [ ] **🎛️ Configurações:** Painel de configuração dos agentes
- [ ] **👥 Multi-usuário:** Permissões e roles

### **Melhorias Técnicas**
- [ ] **WebSockets:** Updates em tempo real
- [ ] **Service Workers:** Cache offline
- [ ] **Lazy Loading:** Carregamento otimizado
- [ ] **Bundle Splitting:** Otimização de performance
- [ ] **E2E Tests:** Testes automatizados com Cypress

## 🆘 Troubleshooting

### **Problemas Comuns**

**1. Mock API não inicia**
```bash
# Verificar dependências
pip install flask flask-cors

# Verificar porta disponível
netstat -an | findstr :5001
```

**2. Frontend não conecta**
```bash
# Verificar URL da API
# Verificar CORS
# Verificar network tabs no DevTools
```

**3. Agentes não respondem**
```bash
# Verificar backend está rodando
# Verificar logs do sistema
# Testar endpoints individualmente
```

**4. Performance lenta**
```bash
# Reduzir intervalo de refresh
# Verificar tamanho do cache
# Otimizar queries da API
```

---

## 📞 Suporte

Para dúvidas e suporte:
1. Consulte os logs do mock API
2. Verifique o console do browser (F12)
3. Teste endpoints individuais
4. Consulte a documentação da API principal

**🎉 Dashboard pronto para uso com monitoramento completo do sistema de agentes!**
