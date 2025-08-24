// Tipos para o Sistema de Auditoria Fiscal ICMS

// Enums
export enum ClassificacaoStatus {
  PENDENTE = 'PENDENTE',
  CLASSIFICADO = 'CLASSIFICADO',
  ERRO = 'ERRO'
}

// Tipos para Relatórios
export interface RelatorioRequest {
  tipo: string;
  formato: 'pdf' | 'excel' | 'csv';
  filtros?: any;
  parametros?: any;
}

// Tipos para respostas da API
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

// Tipos para Dashboard
export interface DashboardStats {
  total_relatorios: number;
  relatorios_pendentes: number;
  relatorios_finalizados: number;
  relatorios_com_erro: number;
  agents_ativos: number;
  agents_executando: number;
}

// Tipos para autenticação
export interface User {
  id: number;
  username: string;
  email: string;
  full_name?: string;
  is_active: boolean;
  created_at: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
  expires_in: number;
}

// Tipos para importação
export interface ImportConfig {
  source_type: 'excel' | 'csv' | 'database';
  file_path?: string;
  database_config?: {
    host: string;
    port: number;
    database: string;
    username: string;
    password: string;
  };
  mapping: {
    [field: string]: string;
  };
}

export interface ImportResult {
  success: boolean;
  total_records: number;
  imported: number;
  updated: number;
  skipped: number;
  errors: number;
  error_details?: string[];
  duration_seconds: number;
}

// Tipos para Produtos
export interface Produto {
  id: string;
  codigo: string;
  descricao: string;
  ncm?: string;
  cest?: string;
  ncm_classificado?: string;
  cest_classificado?: string;
  unidade: string;
  valor_unitario?: number;
  status: ClassificacaoStatus;
  status_classificacao?: ClassificacaoStatus;
  classificacao_manual?: boolean;
  confianca?: number;
  confianca_classificacao?: number;
  observacoes?: string;
  created_at: string;
  updated_at: string;
  empresa_id?: string;
  empresa?: {
    id: string;
    nome: string;
    cnpj: string;
  };
}

export interface ProductFilter {
  search?: string;
  status?: ClassificacaoStatus;
  ncm?: string;
  cest?: string;
  empresa_id?: string;
  page?: number;
  size?: number;
}
