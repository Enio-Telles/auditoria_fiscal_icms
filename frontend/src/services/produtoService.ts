import { Produto, ProductFilter, PaginatedResponse, ApiResponse } from '../types';
import { apiClient } from './apiClient';

export const produtoService = {
  // Listar produtos com filtros
  async listar(filter: ProductFilter = {}): Promise<PaginatedResponse<Produto>> {
    const params = new URLSearchParams();
    
    if (filter.search) params.append('search', filter.search);
    if (filter.status) params.append('status', filter.status);
    if (filter.ncm) params.append('ncm', filter.ncm);
    if (filter.cest) params.append('cest', filter.cest);
    if (filter.empresa_id) params.append('empresa_id', filter.empresa_id);
    if (filter.page) params.append('page', filter.page.toString());
    if (filter.size) params.append('size', filter.size.toString());

    return await apiClient.get<PaginatedResponse<Produto>>(`/produtos?${params.toString()}`);
  },

  // Buscar produto por ID
  async buscarPorId(id: string): Promise<Produto> {
    return await apiClient.get<Produto>(`/produtos/${id}`);
  },

  // Criar novo produto
  async criar(produto: Omit<Produto, 'id' | 'created_at' | 'updated_at'>): Promise<Produto> {
    return await apiClient.post<Produto>('/produtos', produto);
  },

  // Atualizar produto
  async atualizar(id: string, produto: Partial<Produto>): Promise<Produto> {
    return await apiClient.put<Produto>(`/produtos/${id}`, produto);
  },

  // Excluir produto
  async excluir(id: string): Promise<void> {
    await apiClient.delete<void>(`/produtos/${id}`);
  },

  // Reclassificar produto
  async reclassificar(id: string): Promise<Produto> {
    return await apiClient.post<Produto>(`/produtos/${id}/reclassificar`);
  },

  // Upload de arquivo CSV/Excel
  async uploadArquivo(file: File, empresaId?: string): Promise<ApiResponse<any>> {
    const formData = new FormData();
    formData.append('file', file);
    if (empresaId) {
      formData.append('empresa_id', empresaId);
    }

    return await apiClient.post<ApiResponse<any>>('/produtos/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },

  // Classificar produto automaticamente
  async classificar(id: string): Promise<Produto> {
    return await apiClient.post<Produto>(`/produtos/${id}/classificar`);
  },

  // Aprovar classificação automática
  async aprovarClassificacao(id: string): Promise<Produto> {
    return await apiClient.post<Produto>(`/produtos/${id}/aprovar`);
  },

  // Rejeitar classificação automática
  async rejeitarClassificacao(id: string, motivo?: string): Promise<Produto> {
    return await apiClient.post<Produto>(`/produtos/${id}/rejeitar`, {
      motivo
    });
  },

  // Estatísticas de produtos
  async estatisticas(empresaId?: string): Promise<any> {
    const params = empresaId ? `?empresa_id=${empresaId}` : '';
    return await apiClient.get<any>(`/produtos/estatisticas${params}`);
  },

  // Exportar para Excel
  async exportToExcel(filter: ProductFilter = {}): Promise<Blob> {
    const params = new URLSearchParams();
    
    if (filter.search) params.append('search', filter.search);
    if (filter.status) params.append('status', filter.status);
    if (filter.ncm) params.append('ncm', filter.ncm);
    if (filter.cest) params.append('cest', filter.cest);
    if (filter.empresa_id) params.append('empresa_id', filter.empresa_id);

    return await apiClient.get<Blob>(`/produtos/export/excel?${params.toString()}`);
  }
};
