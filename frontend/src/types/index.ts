// Tipos para o Sistema de Auditoria Fiscal ICMS

// Enums
export enum ClassificacaoStatus {
  PENDENTE = 'PENDENTE',
  CLASSIFICADO = 'CLASSIFICADO',
  ERRO = 'ERRO'
}

export enum TipoEmpresa {
  MATRIZ = 'MATRIZ',
  FILIAL = 'FILIAL'
}

export interface Empresa {
  id: string;
  cnpj: string;
  nome: string;
  razao_social?: string;
  nome_fantasia?: string;
  atividade_principal?: string;
  regime_tributario?: string;
  endereco?: any;
  contato?: any;
  ativo: boolean;
  criado_em: string;
  atualizado_em: string;
}

export interface Produto {
  id: number;
  empresa_id: number;
  codigo_produto: string;
  codigo_barras?: string;
  descricao: string;
  ncm?: string;
  cest?: string;
  unidade?: string;
  categoria?: string;
  preco?: number;
  ativo: boolean;
  origem_dados?: string;
  confianca_ncm?: number;
  confianca_cest?: number;
  revisao_manual: boolean;
  criado_em: string;
  atualizado_em: string;
}

export interface NCMClassificacao {
  id: number;
  codigo: string;
  descricao: string;
  capitulo: string;
  posicao: string;
  subposicao: string;
  unidade_estatistica?: string;
  aliquota_ii?: number;
  aliquota_ipi?: number;
  ativo: boolean;
  criado_em: string;
}

export interface CESTClassificacao {
  id: number;
  codigo: string;
  descricao: string;
  segmento: string;
  ncm_vinculados: string[];
  anexo?: string;
  ativo: boolean;
  criado_em: string;
}

export interface AuditoriaClassificacao {
  id: number;
  produto_id: number;
  campo_alterado: string;
  valor_anterior?: string;
  valor_novo?: string;
  motivo?: string;
  usuario?: string;
  confianca?: number;
  origem?: string;
  criado_em: string;
}

export interface WorkflowExecucao {
  id: number;
  empresa_id: number;
  tipo_workflow: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  dados_entrada?: any;
  dados_saida?: any;
  metricas?: any;
  erro?: string;
  iniciado_em: string;
  finalizado_em?: string;
  duracao_segundos?: number;
}

export interface Relatorio {
  id: number;
  empresa_id: number;
  tipo_relatorio: string;
  parametros?: any;
  resultado?: any;
  criado_por?: string;
  criado_em: string;
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
  total_empresas: number;
  total_produtos: number;
  produtos_com_ncm: number;
  produtos_com_cest: number;
  produtos_revisao_manual: number;
  classificacao_accuracy: number;
  workflows_executados: number;
  workflows_sucesso: number;
}

// Tipos para Workflows
export interface WorkflowResult {
  workflow_id: string;
  status: string;
  result?: any;
  error?: string;
  execution_time?: number;
  confidence?: number;
}

export interface ClassificationRequest {
  empresa_id: number;
  produto_codigo: string;
  descricao: string;
  ncm_existente?: string;
  cest_existente?: string;
  workflow_type: 'confirmation' | 'determination';
}

export interface ClassificationResult {
  ncm_result?: {
    codigo: string;
    confianca: number;
    justificativa: string;
  };
  cest_result?: {
    codigo?: string;
    confianca: number;
    justificativa: string;
  };
  requer_revisao_manual: boolean;
  alertas?: string[];
}

// Tipos para Filtros e Busca
export interface ProductFilter {
  empresa_id?: number;
  categoria?: string;
  ncm?: string;
  cest?: string;
  revisao_manual?: boolean;
  sem_ncm?: boolean;
  sem_cest?: boolean;
  search?: string;
}

export interface AuditFilter {
  produto_id?: number;
  campo_alterado?: string;
  origem?: string;
  data_inicio?: string;
  data_fim?: string;
  usuario?: string;
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

// Tipos para formulários
export interface EmpresaForm {
  cnpj: string;
  razao_social: string;
  nome_fantasia?: string;
  atividade_principal?: string;
  regime_tributario?: string;
}

export interface ProdutoForm {
  codigo_produto: string;
  codigo_barras?: string;
  descricao: string;
  ncm?: string;
  cest?: string;
  unidade?: string;
  categoria?: string;
  preco?: number;
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
