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
    return response.data;
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
    return response.data;
  }

  async getEmpresas(): Promise<Array<{ id: string; nome: string }>> {
    const response = await apiClient.get('/empresas/select');
    return response.data;
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
    
    return response.data;
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
    return response.data;
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
    return response.data;
  }

  async getTopNCM(limit: number = 10) {
    const response = await apiClient.get(`/relatorios/top-ncm?limit=${limit}`);
    return response.data;
  }

  async getTopCEST(limit: number = 10) {
    const response = await apiClient.get(`/relatorios/top-cest?limit=${limit}`);
    return response.data;
  }

  async getClassificacaoAccuracy() {
    const response = await apiClient.get('/relatorios/accuracy');
    return response.data;
  }
}

export const relatorioService = new RelatorioService();
