import { apiClient } from './apiClient';
import {
  Empresa,
  EmpresaForm,
  ApiResponse,
  PaginatedResponse,
} from '../types';

export class EmpresaService {
  async getEmpresas(page = 1, size = 10, search?: string): Promise<PaginatedResponse<Empresa>> {
    const params = new URLSearchParams({
      page: page.toString(),
      size: size.toString(),
    });

    if (search) {
      params.append('search', search);
    }

    return apiClient.get<PaginatedResponse<Empresa>>(`/empresas?${params}`);
  }

  async getEmpresaById(id: number): Promise<Empresa> {
    return apiClient.get<Empresa>(`/empresas/${id}`);
  }

  async createEmpresa(empresa: EmpresaForm): Promise<Empresa> {
    return apiClient.post<Empresa>('/empresas', empresa);
  }

  async updateEmpresa(id: number, empresa: Partial<EmpresaForm>): Promise<Empresa> {
    return apiClient.put<Empresa>(`/empresas/${id}`, empresa);
  }

  async deleteEmpresa(id: number): Promise<void> {
    return apiClient.delete<void>(`/empresas/${id}`);
  }

  async getEmpresaStats(id: number): Promise<any> {
    return apiClient.get<any>(`/empresas/${id}/stats`);
  }
}

export const empresaService = new EmpresaService();
