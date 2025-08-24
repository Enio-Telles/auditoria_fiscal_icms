import { apiClient } from './apiClient';

export interface RelatorioStats {
  totalProdutos: number;
  totalClassificados: number;
  totalPendentes: number;
  totalErros: number;
  acuraciaMedia?: number;
  empresas: Array<{
    id: string;
    nome: string;
    totalProdutos: number;
    percentualClassificado: number;
  }>;
}

export interface ClassificacaoPeriodo {
  periodo: string;
  classificados: number;
  pendentes: number;
  erros: number;
}

export interface RelatorioFilter {
  dataInicio?: Date | null;
  dataFim?: Date | null;
  empresaId?: string;
}

export interface ExportRequest extends RelatorioFilter {
  formato: 'pdf' | 'excel';
  tipo: string;
}

// Novas interfaces para relatórios avançados
export interface ExecutiveMetrics {
  totalRevenue: number;
  complianceScore: number;
  riskLevel: 'low' | 'medium' | 'high';
  automationRate: number;
  trends: {
    revenue: number;
    compliance: number;
    automation: number;
  };
}

export interface PerformanceMetrics {
  systemUptime: number;
  processingSpeed: number;
  accuracyRate: number;
  errorRate: number;
  agentMetrics: Array<{
    agentName: string;
    performance: number;
    status: 'active' | 'inactive' | 'error';
  }>;
}

export interface ComplianceMetrics {
  overallScore: number;
  riskAreas: Array<{
    area: string;
    riskLevel: 'low' | 'medium' | 'high' | 'critical';
    affectedItems: number;
  }>;
  auditTrail: Array<{
    date: string;
    action: string;
    user: string;
    impact: 'low' | 'medium' | 'high';
  }>;
}

export interface ProductivityReport {
  timeRange: string;
  totalProcessed: number;
  avgProcessingTime: number;
  userProductivity: Array<{
    userId: string;
    userName: string;
    itemsProcessed: number;
    accuracyRate: number;
  }>;
}

export interface NCMAnalysis {
  topNCMs: Array<{
    code: string;
    description: string;
    frequency: number;
    accuracyRate: number;
  }>;
  problematicNCMs: Array<{
    code: string;
    description: string;
    errorRate: number;
    commonErrors: string[];
  }>;
}

class RelatorioService {
  async getStats(filter: RelatorioFilter): Promise<RelatorioStats> {
    const params = new URLSearchParams();
    
    if (filter.dataInicio) {
      params.append('data_inicio', filter.dataInicio.toISOString().split('T')[0]);
    }
    if (filter.dataFim) {
      params.append('data_fim', filter.dataFim.toISOString().split('T')[0]);
    }
    if (filter.empresaId) {
      params.append('empresa_id', filter.empresaId);
    }

    const response = await apiClient.get(`/relatorios/stats?${params.toString()}`);
    return (response as any).data;
  }

  async getClassificacaoPorPeriodo(filter: RelatorioFilter): Promise<ClassificacaoPeriodo[]> {
    const params = new URLSearchParams();
    
    if (filter.dataInicio) {
      params.append('data_inicio', filter.dataInicio.toISOString().split('T')[0]);
    }
    if (filter.dataFim) {
      params.append('data_fim', filter.dataFim.toISOString().split('T')[0]);
    }
    if (filter.empresaId) {
      params.append('empresa_id', filter.empresaId);
    }

    const response = await apiClient.get(`/relatorios/classificacao-periodo?${params.toString()}`);
    return (response as any).data;
  }

  async getEmpresas(): Promise<Array<{ id: string; nome: string }>> {
    const response = await apiClient.get('/empresas/select');
    return (response as any).data;
  }

  async exportar(request: ExportRequest): Promise<Blob> {
    const params = new URLSearchParams();
    
    params.append('formato', request.formato);
    params.append('tipo', request.tipo);
    
    if (request.dataInicio) {
      params.append('data_inicio', request.dataInicio.toISOString().split('T')[0]);
    }
    if (request.dataFim) {
      params.append('data_fim', request.dataFim.toISOString().split('T')[0]);
    }
    if (request.empresaId) {
      params.append('empresa_id', request.empresaId);
    }

    const response = await apiClient.get(`/relatorios/exportar?${params.toString()}`, {
      responseType: 'blob',
    });
    
    return (response as any).data;
  }

  async getConformidadeReport(filter: RelatorioFilter) {
    const params = new URLSearchParams();
    
    if (filter.dataInicio) {
      params.append('data_inicio', filter.dataInicio.toISOString().split('T')[0]);
    }
    if (filter.dataFim) {
      params.append('data_fim', filter.dataFim.toISOString().split('T')[0]);
    }
    if (filter.empresaId) {
      params.append('empresa_id', filter.empresaId);
    }

    const response = await apiClient.get(`/relatorios/conformidade?${params.toString()}`);
    return (response as any).data;
  }

  async getProdutividadeReport(filter: RelatorioFilter) {
    const params = new URLSearchParams();
    
    if (filter.dataInicio) {
      params.append('data_inicio', filter.dataInicio.toISOString().split('T')[0]);
    }
    if (filter.dataFim) {
      params.append('data_fim', filter.dataFim.toISOString().split('T')[0]);
    }
    if (filter.empresaId) {
      params.append('empresa_id', filter.empresaId);
    }

    const response = await apiClient.get(`/relatorios/produtividade?${params.toString()}`);
    return (response as any).data;
  }

  async getTopNCM(limit: number = 10) {
    const response = await apiClient.get(`/relatorios/top-ncm?limit=${limit}`);
    return (response as any).data;
  }

  async getTopCEST(limit: number = 10) {
    const response = await apiClient.get(`/relatorios/top-cest?limit=${limit}`);
    return (response as any).data;
  }

  async getClassificacaoAccuracy() {
    const response = await apiClient.get('/relatorios/accuracy');
    return (response as any).data;
  }

  // Novos métodos para relatórios avançados
  async getExecutiveMetrics(filter: RelatorioFilter): Promise<ExecutiveMetrics> {
    const params = new URLSearchParams();
    
    if (filter.dataInicio) {
      params.append('data_inicio', filter.dataInicio.toISOString().split('T')[0]);
    }
    if (filter.dataFim) {
      params.append('data_fim', filter.dataFim.toISOString().split('T')[0]);
    }
    if (filter.empresaId) {
      params.append('empresa_id', filter.empresaId);
    }

    const response = await apiClient.get(`/relatorios/executive-metrics?${params.toString()}`);
    return (response as any).data;
  }

  async getPerformanceMetrics(filter: RelatorioFilter): Promise<PerformanceMetrics> {
    const params = new URLSearchParams();
    
    if (filter.dataInicio) {
      params.append('data_inicio', filter.dataInicio.toISOString().split('T')[0]);
    }
    if (filter.dataFim) {
      params.append('data_fim', filter.dataFim.toISOString().split('T')[0]);
    }

    const response = await apiClient.get(`/relatorios/performance-metrics?${params.toString()}`);
    return (response as any).data;
  }

  async getComplianceMetrics(filter: RelatorioFilter): Promise<ComplianceMetrics> {
    const params = new URLSearchParams();
    
    if (filter.dataInicio) {
      params.append('data_inicio', filter.dataInicio.toISOString().split('T')[0]);
    }
    if (filter.dataFim) {
      params.append('data_fim', filter.dataFim.toISOString().split('T')[0]);
    }
    if (filter.empresaId) {
      params.append('empresa_id', filter.empresaId);
    }

    const response = await apiClient.get(`/relatorios/compliance-metrics?${params.toString()}`);
    return (response as any).data;
  }

  async getProductivityReport(filter: RelatorioFilter): Promise<ProductivityReport> {
    const params = new URLSearchParams();
    
    if (filter.dataInicio) {
      params.append('data_inicio', filter.dataInicio.toISOString().split('T')[0]);
    }
    if (filter.dataFim) {
      params.append('data_fim', filter.dataFim.toISOString().split('T')[0]);
    }
    if (filter.empresaId) {
      params.append('empresa_id', filter.empresaId);
    }

    const response = await apiClient.get(`/relatorios/productivity?${params.toString()}`);
    return (response as any).data;
  }

  async getNCMAnalysis(filter: RelatorioFilter): Promise<NCMAnalysis> {
    const params = new URLSearchParams();
    
    if (filter.dataInicio) {
      params.append('data_inicio', filter.dataInicio.toISOString().split('T')[0]);
    }
    if (filter.dataFim) {
      params.append('data_fim', filter.dataFim.toISOString().split('T')[0]);
    }
    if (filter.empresaId) {
      params.append('empresa_id', filter.empresaId);
    }

    const response = await apiClient.get(`/relatorios/ncm-analysis?${params.toString()}`);
    return (response as any).data;
  }

  async getSystemHealth(): Promise<any> {
    const response = await apiClient.get('/relatorios/system-health');
    return (response as any).data;
  }

  async getAuditLog(filter: RelatorioFilter & { userId?: string; action?: string }): Promise<any> {
    const params = new URLSearchParams();
    
    if (filter.dataInicio) {
      params.append('data_inicio', filter.dataInicio.toISOString().split('T')[0]);
    }
    if (filter.dataFim) {
      params.append('data_fim', filter.dataFim.toISOString().split('T')[0]);
    }
    if (filter.empresaId) {
      params.append('empresa_id', filter.empresaId);
    }
    if (filter.userId) {
      params.append('user_id', filter.userId);
    }
    if (filter.action) {
      params.append('action', filter.action);
    }

    const response = await apiClient.get(`/relatorios/audit-log?${params.toString()}`);
    return (response as any).data;
  }

  async generateCustomReport(config: {
    type: 'executive' | 'operational' | 'compliance' | 'performance';
    metrics: string[];
    filters: RelatorioFilter;
    format: 'pdf' | 'excel' | 'json';
  }): Promise<any> {
    const response = await apiClient.post('/relatorios/custom', config);
    return (response as any).data;
  }

  async scheduleReport(schedule: {
    name: string;
    type: string;
    frequency: 'daily' | 'weekly' | 'monthly';
    recipients: string[];
    filters: RelatorioFilter;
  }): Promise<any> {
    const response = await apiClient.post('/relatorios/schedule', schedule);
    return (response as any).data;
  }

  async getScheduledReports(): Promise<any> {
    const response = await apiClient.get('/relatorios/scheduled');
    return (response as any).data;
  }
}

export const relatorioService = new RelatorioService();
