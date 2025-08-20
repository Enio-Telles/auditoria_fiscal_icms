import { apiClient } from './apiClient';
import {
  Produto,
  ProdutoForm,
  ProductFilter,
  ClassificationRequest,
  ClassificationResult,
  WorkflowResult,
  PaginatedResponse,
} from '../types';

export class ProdutoService {
  async getProdutos(
    filter: ProductFilter = {},
    page = 1,
    size = 10
  ): Promise<PaginatedResponse<Produto>> {
    const params = new URLSearchParams({
      page: page.toString(),
      size: size.toString(),
    });

    // Adicionar filtros
    Object.entries(filter).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        params.append(key, value.toString());
      }
    });

    return apiClient.get<PaginatedResponse<Produto>>(`/produtos?${params}`);
  }

  async getProdutoById(id: number): Promise<Produto> {
    return apiClient.get<Produto>(`/produtos/${id}`);
  }

  async createProduto(empresaId: number, produto: ProdutoForm): Promise<Produto> {
    return apiClient.post<Produto>(`/empresas/${empresaId}/produtos`, produto);
  }

  async updateProduto(id: number, produto: Partial<ProdutoForm>): Promise<Produto> {
    return apiClient.put<Produto>(`/produtos/${id}`, produto);
  }

  async deleteProduto(id: number): Promise<void> {
    return apiClient.delete<void>(`/produtos/${id}`);
  }

  async importProdutos(empresaId: number, file: File): Promise<any> {
    return apiClient.uploadFile<any>(`/empresas/${empresaId}/produtos/import`, file);
  }

  async exportProdutos(empresaId: number, format = 'excel'): Promise<Blob> {
    const response = await apiClient.get<Blob>(
      `/empresas/${empresaId}/produtos/export?format=${format}`,
      { responseType: 'blob' }
    );
    return response;
  }

  // Classificação automática
  async classifyProduct(request: ClassificationRequest): Promise<ClassificationResult> {
    return apiClient.post<ClassificationResult>('/classify', request);
  }

  async executeWorkflow(workflowType: string, params: any): Promise<WorkflowResult> {
    return apiClient.post<WorkflowResult>(`/workflows/${workflowType}/execute`, params);
  }

  async getWorkflowStatus(workflowId: string): Promise<WorkflowResult> {
    return apiClient.get<WorkflowResult>(`/workflows/${workflowId}/status`);
  }

  // Processamento em lote
  async processEmpresaProdutos(empresaId: number): Promise<any> {
    return apiClient.post<any>(`/empresas/${empresaId}/processar`);
  }

  async getProcessingStatus(empresaId: number): Promise<any> {
    return apiClient.get<any>(`/empresas/${empresaId}/processing-status`);
  }
}

export const produtoService = new ProdutoService();
