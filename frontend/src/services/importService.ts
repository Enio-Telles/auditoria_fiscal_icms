import axios, { AxiosInstance } from 'axios';

// Interface para configuração de conexão de banco
export interface DatabaseConnection {
  type: 'postgresql' | 'sqlserver' | 'mysql';
  host: string;
  port: number;
  database: string;
  user: string;
  password: string;
  schema?: string;
}

// Interface para resultado de teste de conexão
export interface ConnectionTestResult {
  success: boolean;
  message?: string;
  database?: string;
  host?: string;
  database_info?: string;
  error?: string;
}

// Interface para preview de dados
export interface DataPreview {
  success: boolean;
  preview_count: number;
  total_estimated?: number;
  columns: string[];
  data: Record<string, any>[];
  error?: string;
}

// Interface para resultado de importação
export interface ImportResult {
  success: boolean;
  records_imported: number;
  records_with_errors: number;
  execution_time: number;
  summary: {
    empresas: number;
    produtos: number;
    ncm_matches: number;
    cest_matches: number;
  };
  errors?: string[];
}

// Interface para estatísticas do sistema
export interface SystemStats {
  total_empresas: number;
  total_produtos: number;
  versao: string;
  status: string;
  golden_set: {
    ncm_items: number;
    cest_items: number;
  };
  arquitetura: string;
  database: {
    type: string;
    status: string;
  };
}

class ImportService {
  private client: AxiosInstance;

  constructor() {
    // Conecta diretamente com a API estável na porta 8003
    this.client = axios.create({
      baseURL: 'http://localhost:8003',
      timeout: 60000, // 60 segundos para operações de importação
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Interceptor para logs de debug
    this.client.interceptors.request.use(
      (config) => {
        console.log(`🔄 API Request: ${config.method?.toUpperCase()} ${config.url}`);
        return config;
      },
      (error) => {
        console.error('❌ API Request Error:', error);
        return Promise.reject(error);
      }
    );

    this.client.interceptors.response.use(
      (response) => {
        console.log(`✅ API Response: ${response.status} ${response.config.url}`);
        return response;
      },
      (error) => {
        console.error('❌ API Response Error:', error.response?.data || error.message);
        return Promise.reject(error);
      }
    );
  }

  // Verifica se a API está funcionando
  async checkHealth() {
    try {
      const response = await this.client.get('/health');
      return response.data;
    } catch (error) {
      console.error('Erro ao verificar saúde da API:', error);
      throw error;
    }
  }

  // Obtém estatísticas do sistema
  async getSystemStats(): Promise<SystemStats> {
    try {
      const response = await this.client.get('/stats');
      return response.data;
    } catch (error) {
      console.error('Erro ao obter estatísticas:', error);
      throw error;
    }
  }

  // Lista empresas cadastradas
  async getEmpresas() {
    try {
      const response = await this.client.get('/empresas');
      return response.data;
    } catch (error) {
      console.error('Erro ao listar empresas:', error);
      throw error;
    }
  }

  // Testa conexão com banco de dados
  async testConnection(connection: DatabaseConnection): Promise<ConnectionTestResult> {
    try {
      const response = await this.client.post('/api/import/test-connection', connection);
      return response.data;
    } catch (error) {
      console.error('Erro ao testar conexão:', error);
      throw error;
    }
  }

  // Faz preview dos dados que serão importados
  async previewData(
    connection: DatabaseConnection,
    sqlQuery: string,
    limit: number = 10
  ): Promise<DataPreview> {
    try {
      const response = await this.client.post(
        `/api/import/preview?sql_query=${encodeURIComponent(sqlQuery)}&limit=${limit}`,
        connection
      );
      return response.data;
    } catch (error) {
      console.error('Erro ao fazer preview:', error);
      throw error;
    }
  }

  // Executa importação completa
  async executeImport(
    connection: DatabaseConnection,
    sqlQuery: string,
    empresa_id?: string
  ): Promise<ImportResult> {
    try {
      const params = new URLSearchParams({
        sql_query: sqlQuery,
      });

      if (empresa_id) {
        params.append('empresa_id', empresa_id);
      }

      const response = await this.client.post(
        `/api/import/execute?${params.toString()}`,
        connection
      );
      return response.data;
    } catch (error) {
      console.error('Erro ao executar importação:', error);
      throw error;
    }
  }

  // Consultas SQL predefinidas
  getPresetQueries() {
    return {
      postgresql: {
        basic: "SELECT produto_id, descricao_produto, ncm, cest FROM dbo.produto LIMIT 1000",
        complete: `
          SELECT
            produto_id,
            descricao_produto,
            ncm,
            cest,
            preco_unitario,
            unidade_medida,
            categoria,
            subcategoria
          FROM dbo.produto
          WHERE descricao_produto IS NOT NULL
            AND ncm IS NOT NULL
          ORDER BY produto_id
        `.trim(),
        with_company: `
          SELECT
            p.produto_id,
            p.descricao_produto,
            p.ncm,
            p.cest,
            e.razao_social,
            e.cnpj
          FROM dbo.produto p
          LEFT JOIN dbo.empresa e ON p.empresa_id = e.empresa_id
          WHERE p.descricao_produto IS NOT NULL
        `.trim()
      },
      sqlserver: {
        basic: "SELECT TOP 1000 produto_id, descricao_produto, ncm, cest FROM dbo.produto",
        complete: `
          SELECT TOP 10000
            produto_id,
            descricao_produto,
            ncm,
            cest,
            preco_unitario,
            unidade_medida,
            categoria,
            subcategoria
          FROM dbo.produto
          WHERE descricao_produto IS NOT NULL
            AND ncm IS NOT NULL
          ORDER BY produto_id
        `.trim()
      },
      mysql: {
        basic: "SELECT produto_id, descricao_produto, ncm, cest FROM produto LIMIT 1000",
        complete: `
          SELECT
            produto_id,
            descricao_produto,
            ncm,
            cest,
            preco_unitario,
            unidade_medida,
            categoria,
            subcategoria
          FROM produto
          WHERE descricao_produto IS NOT NULL
            AND ncm IS NOT NULL
          ORDER BY produto_id
          LIMIT 10000
        `.trim()
      }
    };
  }
}

// Instância singleton do serviço
export const importService = new ImportService();

export default ImportService;
