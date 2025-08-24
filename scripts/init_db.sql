-- Script de inicialização do PostgreSQL
-- Sistema de Auditoria Fiscal ICMS v15.0

-- Comentário: Databases são criados pelo docker-compose

-- Ativa extensões necessárias
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS btree_gin;

-- Configurações iniciais
SET timezone = 'America/Sao_Paulo';

-- Função para criar índices de performance
CREATE OR REPLACE FUNCTION create_performance_indexes() RETURNS void AS $$
BEGIN
    -- Índices para busca textual
    CREATE INDEX IF NOT EXISTS idx_ncm_descricao_gin
        ON ncm USING gin(to_tsvector('portuguese', descricao));

    CREATE INDEX IF NOT EXISTS idx_golden_set_descricao_gin
        ON golden_set USING gin(to_tsvector('portuguese', descricao_produto || ' ' || descricao_enriquecida));

    CREATE INDEX IF NOT EXISTS idx_produtos_exemplos_descricao_gin
        ON produtos_exemplos USING gin(to_tsvector('portuguese', descricao));

    -- Índices compostos para queries frequentes
    CREATE INDEX IF NOT EXISTS idx_mercadoria_empresa_status_data
        ON mercadorias_a_classificar(empresa_id, status, criado_em DESC);

    CREATE INDEX IF NOT EXISTS idx_classificacao_confianca_ncm_cest
        ON classificacoes(confianca_ncm DESC, confianca_cest DESC, ncm_determinado, cest_determinado);

    -- Índices para relacionamentos
    CREATE INDEX IF NOT EXISTS idx_ncm_cest_assoc_pattern_tipo
        ON ncm_cest_associacao(ncm_pattern, tipo_associacao, nivel_hierarquia);

    RAISE NOTICE 'Índices de performance criados com sucesso!';
END;
$$ LANGUAGE plpgsql;

-- Função para inserir dados iniciais
CREATE OR REPLACE FUNCTION insert_initial_data() RETURNS void AS $$
BEGIN
    -- Insere usuário administrador padrão se não existir
    INSERT INTO usuarios (nome, email, senha_hash, ativo)
    SELECT 'Administrador', 'admin@auditoria.local',
           '$2b$12$LQv3c1yqBwFNXF/wCKF.cOzJmzF.wC4vKZD3jCJX7VF4wQ1qKxgWG', true
    WHERE NOT EXISTS (SELECT 1 FROM usuarios WHERE email = 'admin@auditoria.local');

    -- Insere empresa exemplo se não existir
    INSERT INTO empresas (nome, cnpj, uf, segmento_fiscal, ativa)
    SELECT 'Empresa Exemplo LTDA', '12345678000195', 'SP', 'Comércio Varejista', true
    WHERE NOT EXISTS (SELECT 1 FROM empresas WHERE cnpj = '12345678000195');

    RAISE NOTICE 'Dados iniciais inseridos com sucesso!';
END;
$$ LANGUAGE plpgsql;

-- Função para validar integridade dos dados
CREATE OR REPLACE FUNCTION validate_data_integrity() RETURNS TABLE (
    tabela VARCHAR,
    total_registros BIGINT,
    status VARCHAR
) AS $$
DECLARE
    rec RECORD;
BEGIN
    -- Valida tabelas principais
    FOR rec IN
        SELECT t.table_name
        FROM information_schema.tables t
        WHERE t.table_schema = 'public'
        AND t.table_type = 'BASE TABLE'
        AND t.table_name IN ('ncm', 'cest_regras', 'segmentos', 'produtos_exemplos',
                           'ncm_cest_associacao', 'golden_set', 'usuarios', 'empresas')
    LOOP
        EXECUTE format('SELECT COUNT(*) FROM %I', rec.table_name) INTO total_registros;

        tabela := rec.table_name;

        IF total_registros > 0 THEN
            status := 'OK';
        ELSE
            status := 'VAZIO';
        END IF;

        RETURN NEXT;
    END LOOP;

    RETURN;
END;
$$ LANGUAGE plpgsql;

-- Executa funções de inicialização
SELECT create_performance_indexes();
SELECT insert_initial_data();

-- Exibe status das tabelas
SELECT * FROM validate_data_integrity();
