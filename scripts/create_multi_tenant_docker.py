"""
Script para configurar bancos multi-tenant via comandos Docker
Executa comandos SQL diretamente no container PostgreSQL
"""

import subprocess


def run_docker_command(sql_command, database="postgres"):
    """Executa comando SQL no container PostgreSQL"""
    docker_cmd = [
        "docker",
        "exec",
        "auditoria_postgresql",
        "psql",
        "-U",
        "postgres",
        "-d",
        database,
        "-c",
        sql_command,
    ]

    try:
        result = subprocess.run(docker_cmd, capture_output=True, text=True, check=True)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr


def create_database_docker(db_name):
    """Cria banco de dados via Docker"""
    print(f"Criando banco: {db_name}")

    # Verificar se banco existe
    check_sql = f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{db_name}'"
    success, output = run_docker_command(check_sql)

    if success and "1" in output:
        print(f"ℹ️  Banco '{db_name}' já existe")
        return True

    # Criar banco
    create_sql = f'CREATE DATABASE "{db_name}"'
    success, output = run_docker_command(create_sql)

    if success:
        print(f"✅ Banco '{db_name}' criado com sucesso!")
        return True
    else:
        print(f"❌ Erro ao criar banco '{db_name}': {output}")
        return False


def create_table_in_database(db_name, table_sql):
    """Cria tabela em banco específico"""
    success, output = run_docker_command(table_sql, database=db_name)

    if success:
        return True
    else:
        print(f"❌ Erro ao criar tabela em '{db_name}': {output}")
        return False


def setup_central_database():
    """Configura banco central"""
    print("\n🏢 Configurando banco CENTRAL...")

    if not create_database_docker("auditoria_central"):
        return False

    # SQL para criar tabelas do banco central
    usuarios_sql = """
    CREATE TABLE IF NOT EXISTS usuarios (
        id SERIAL PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        email VARCHAR(100) UNIQUE NOT NULL,
        senha_hash VARCHAR(255) NOT NULL,
        nome_completo VARCHAR(100),
        ativo BOOLEAN DEFAULT TRUE,
        admin BOOLEAN DEFAULT FALSE,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        ultimo_login TIMESTAMP
    );
    """

    empresas_sql = """
    CREATE TABLE IF NOT EXISTS empresas (
        id SERIAL PRIMARY KEY,
        cnpj VARCHAR(18) UNIQUE NOT NULL,
        razao_social VARCHAR(200) NOT NULL,
        nome_fantasia VARCHAR(200),
        endereco TEXT,
        cidade VARCHAR(100),
        estado VARCHAR(2),
        cep VARCHAR(10),
        telefone VARCHAR(20),
        email VARCHAR(100),
        atividade_principal VARCHAR(10),
        regime_tributario VARCHAR(20),
        database_name VARCHAR(100) NOT NULL,
        ativa BOOLEAN DEFAULT TRUE,
        criada_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        atualizada_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """

    permissoes_sql = """
    CREATE TABLE IF NOT EXISTS permissoes_empresa (
        id SERIAL PRIMARY KEY,
        usuario_id INTEGER REFERENCES usuarios(id),
        empresa_id INTEGER REFERENCES empresas(id),
        nivel_acesso VARCHAR(20),
        criada_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """

    # Criar tabelas
    tables = [
        ("usuarios", usuarios_sql),
        ("empresas", empresas_sql),
        ("permissoes_empresa", permissoes_sql),
    ]

    for table_name, sql in tables:
        if create_table_in_database("auditoria_central", sql):
            print(f"✅ Tabela '{table_name}' criada no banco central")
        else:
            return False

    return True


def setup_golden_set_database():
    """Configura banco do Golden Set"""
    print("\n🏆 Configurando banco GOLDEN SET...")

    if not create_database_docker("golden_set"):
        return False

    # SQL para tabelas do Golden Set
    golden_ncm_sql = """
    CREATE TABLE IF NOT EXISTS golden_set_ncm (
        id SERIAL PRIMARY KEY,
        produto_nome TEXT NOT NULL,
        produto_descricao TEXT,
        categoria VARCHAR(100),
        marca VARCHAR(100),
        ncm_codigo VARCHAR(10) NOT NULL,
        ncm_descricao TEXT,
        confianca NUMERIC(5,2) DEFAULT 100.0,
        fonte VARCHAR(100),
        validado_por VARCHAR(100),
        validado_em TIMESTAMP,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        ativo BOOLEAN DEFAULT TRUE
    );
    """

    golden_cest_sql = """
    CREATE TABLE IF NOT EXISTS golden_set_cest (
        id SERIAL PRIMARY KEY,
        ncm_codigo VARCHAR(10) NOT NULL,
        cest_codigo VARCHAR(7) NOT NULL,
        cest_descricao TEXT,
        estado VARCHAR(2),
        atividade_cnae VARCHAR(10),
        confianca NUMERIC(5,2) DEFAULT 100.0,
        fonte VARCHAR(100),
        validado_por VARCHAR(100),
        validado_em TIMESTAMP,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        ativo BOOLEAN DEFAULT TRUE
    );
    """

    # Criar tabelas
    tables = [("golden_set_ncm", golden_ncm_sql), ("golden_set_cest", golden_cest_sql)]

    for table_name, sql in tables:
        if create_table_in_database("golden_set", sql):
            print(f"✅ Tabela '{table_name}' criada no Golden Set")
        else:
            return False

    return True


def create_empresa_database(cnpj_clean, razao_social):
    """Cria banco específico para empresa"""
    db_name = f"empresa_{cnpj_clean}"

    print(f"\n🏭 Criando banco para: {razao_social}")
    print(f"   Banco: {db_name}")

    if not create_database_docker(db_name):
        return None

    # SQL para tabelas da empresa
    produtos_sql = """
    CREATE TABLE IF NOT EXISTS produtos (
        id SERIAL PRIMARY KEY,
        codigo_interno VARCHAR(50),
        ean VARCHAR(20),
        nome TEXT NOT NULL,
        descricao TEXT,
        categoria VARCHAR(100),
        subcategoria VARCHAR(100),
        marca VARCHAR(100),
        modelo VARCHAR(100),
        unidade VARCHAR(10),
        preco_custo NUMERIC(12,2),
        preco_venda NUMERIC(12,2),
        estoque_atual INTEGER,
        ncm_codigo VARCHAR(10),
        cest_codigo VARCHAR(7),
        origem VARCHAR(1),
        cst_icms VARCHAR(3),
        aliquota_icms NUMERIC(5,2),
        ativo BOOLEAN DEFAULT TRUE,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """

    classificacoes_sql = """
    CREATE TABLE IF NOT EXISTS classificacoes_ia (
        id SERIAL PRIMARY KEY,
        produto_id INTEGER REFERENCES produtos(id),
        ncm_sugerido VARCHAR(10),
        ncm_confianca NUMERIC(5,2),
        cest_sugerido VARCHAR(7),
        cest_confianca NUMERIC(5,2),
        justificativa TEXT,
        agente_usado VARCHAR(50),
        status VARCHAR(20),
        processado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        aprovado_por VARCHAR(100),
        aprovado_em TIMESTAMP
    );
    """

    auditoria_sql = """
    CREATE TABLE IF NOT EXISTS auditoria_classificacoes (
        id SERIAL PRIMARY KEY,
        produto_id INTEGER REFERENCES produtos(id),
        ncm_anterior VARCHAR(10),
        ncm_novo VARCHAR(10),
        cest_anterior VARCHAR(7),
        cest_novo VARCHAR(7),
        motivo_alteracao TEXT,
        usuario VARCHAR(100),
        alterado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """

    # Criar tabelas
    tables = [
        ("produtos", produtos_sql),
        ("classificacoes_ia", classificacoes_sql),
        ("auditoria_classificacoes", auditoria_sql),
    ]

    for table_name, sql in tables:
        if create_table_in_database(db_name, sql):
            print(f"✅ Tabela '{table_name}' criada em {db_name}")
        else:
            return None

    return db_name


def insert_admin_user():
    """Insere usuário administrador"""
    insert_sql = """
    INSERT INTO usuarios (username, email, senha_hash, nome_completo, admin)
    VALUES ('admin', 'admin@auditoria.com', 'admin123', 'Administrador do Sistema', TRUE)
    ON CONFLICT (username) DO NOTHING;
    """

    success, output = run_docker_command(insert_sql, "auditoria_central")

    if success:
        print("✅ Usuário admin criado/verificado")
        return True
    else:
        print(f"❌ Erro ao criar usuário admin: {output}")
        return False


def insert_sample_empresa(
    cnpj, razao_social, nome_fantasia, atividade, regime, db_name
):
    """Insere empresa no banco central"""
    insert_sql = f"""
    INSERT INTO empresas (cnpj, razao_social, nome_fantasia, atividade_principal, regime_tributario, database_name)
    VALUES ('{cnpj}', '{razao_social}', '{nome_fantasia}', '{atividade}', '{regime}', '{db_name}')
    ON CONFLICT (cnpj) DO NOTHING;
    """

    success, output = run_docker_command(insert_sql, "auditoria_central")

    if success:
        print(f"✅ Empresa registrada: {razao_social}")
        return True
    else:
        print(f"❌ Erro ao registrar empresa: {output}")
        return False


def setup_sample_companies():
    """Cria empresas de exemplo"""
    empresas = [
        {
            "cnpj": "12.345.678/0001-90",
            "cnpj_clean": "12345678000190",
            "razao_social": "ABC Farmácia Ltda",
            "nome_fantasia": "Farmácia ABC",
            "atividade": "4771700",
            "regime": "Simples Nacional",
        },
        {
            "cnpj": "98.765.432/0001-10",
            "cnpj_clean": "98765432000110",
            "razao_social": "Tech Solutions Informática Ltda",
            "nome_fantasia": "Tech Solutions",
            "atividade": "4751200",
            "regime": "Lucro Presumido",
        },
        {
            "cnpj": "11.222.333/0001-44",
            "cnpj_clean": "11222333000144",
            "razao_social": "SuperMercado Central Ltda",
            "nome_fantasia": "SuperMercado Central",
            "atividade": "4711301",
            "regime": "Lucro Real",
        },
    ]

    print("\n🏪 Criando empresas de exemplo...")

    for empresa in empresas:
        # Criar banco da empresa
        db_name = create_empresa_database(
            empresa["cnpj_clean"], empresa["razao_social"]
        )

        if db_name:
            # Registrar no banco central
            insert_sample_empresa(
                empresa["cnpj"],
                empresa["razao_social"],
                empresa["nome_fantasia"],
                empresa["atividade"],
                empresa["regime"],
                db_name,
            )


def list_databases():
    """Lista todos os bancos criados"""
    list_sql = (
        "SELECT datname FROM pg_database WHERE datistemplate = false ORDER BY datname;"
    )
    success, output = run_docker_command(list_sql)

    if success:
        print("\n📊 Bancos de dados criados:")
        lines = output.strip().split("\n")
        for line in lines:
            if (
                line.strip()
                and not line.startswith("datname")
                and not line.startswith("---")
            ):
                db_name = line.strip()
                if (
                    "auditoria" in db_name
                    or "golden" in db_name
                    or "empresa" in db_name
                ):
                    print(f"   • {db_name}")


def main():
    """Execução principal"""
    print("🚀 CONFIGURAÇÃO MULTI-TENANT VIA DOCKER")
    print("=" * 60)

    # 1. Configurar banco central
    if not setup_central_database():
        print("❌ Falha na configuração do banco central!")
        return

    # 2. Configurar Golden Set
    if not setup_golden_set_database():
        print("❌ Falha na configuração do Golden Set!")
        return

    # 3. Criar usuário admin
    insert_admin_user()

    # 4. Criar empresas de exemplo
    setup_sample_companies()

    # 5. Listar bancos criados
    list_databases()

    print("\n" + "=" * 60)
    print("🎉 CONFIGURAÇÃO MULTI-TENANT CONCLUÍDA!")
    print("\n🔐 Acesso:")
    print("   • Host: localhost:5432")
    print("   • Usuário: postgres")
    print("   • Senha: postgres123")
    print("   • Login Sistema: admin / admin123")


if __name__ == "__main__":
    main()
