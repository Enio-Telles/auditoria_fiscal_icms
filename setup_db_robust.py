"""
Script robusto de configuração do banco PostgreSQL
Conecta diretamente no container Docker para evitar problemas de autenticação
"""

import subprocess
import sys
import time
from pathlib import Path

def run_docker_command(command, description):
    """Executa comando no container PostgreSQL"""
    print(f"🔄 {description}...")
    
    full_command = f'docker exec auditoria_postgresql psql -U postgres -d auditoria_fiscal -c "{command}"'
    
    try:
        result = subprocess.run(
            full_command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print(f"✅ {description} - Sucesso!")
            if result.stdout.strip():
                print(f"📝 Resultado: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ {description} - Erro!")
            print(f"🔍 Erro: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} - Timeout!")
        return False
    except Exception as e:
        print(f"💥 {description} - Exceção: {e}")
        return False

def create_basic_tables():
    """Cria tabelas básicas do sistema"""
    
    tables = [
        {
            "name": "usuarios",
            "sql": """
                CREATE TABLE IF NOT EXISTS usuarios (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """
        },
        {
            "name": "empresas", 
            "sql": """
                CREATE TABLE IF NOT EXISTS empresas (
                    id SERIAL PRIMARY KEY,
                    cnpj VARCHAR(14) UNIQUE NOT NULL,
                    razao_social VARCHAR(255) NOT NULL,
                    nome_fantasia VARCHAR(255),
                    atividade_principal VARCHAR(10),
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """
        },
        {
            "name": "produtos",
            "sql": """
                CREATE TABLE IF NOT EXISTS produtos (
                    id SERIAL PRIMARY KEY,
                    empresa_id INTEGER REFERENCES empresas(id),
                    codigo_produto VARCHAR(50),
                    nome TEXT NOT NULL,
                    descricao TEXT,
                    categoria VARCHAR(100),
                    ncm_atual VARCHAR(8),
                    cest_atual VARCHAR(7),
                    preco DECIMAL(10,2),
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """
        },
        {
            "name": "classificacoes",
            "sql": """
                CREATE TABLE IF NOT EXISTS classificacoes (
                    id SERIAL PRIMARY KEY,
                    produto_id INTEGER REFERENCES produtos(id),
                    ncm_sugerido VARCHAR(8),
                    ncm_confidence DECIMAL(5,4),
                    cest_sugerido VARCHAR(7),
                    cest_confidence DECIMAL(5,4),
                    status VARCHAR(20) DEFAULT 'PENDENTE',
                    justificativa TEXT,
                    reviewed_by INTEGER REFERENCES usuarios(id),
                    reviewed_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """
        }
    ]
    
    success_count = 0
    for table in tables:
        if run_docker_command(table["sql"], f"Criando tabela {table['name']}"):
            success_count += 1
        time.sleep(1)  # Pausa entre comandos
    
    return success_count == len(tables)

def insert_test_data():
    """Insere dados de teste"""
    
    test_data = [
        {
            "description": "Inserindo usuário admin",
            "sql": """
                INSERT INTO usuarios (username, email, password_hash) 
                VALUES ('admin', 'admin@auditoria.com', '$2b$12$dummy_hash_for_testing') 
                ON CONFLICT (username) DO NOTHING;
            """
        },
        {
            "description": "Inserindo empresa teste",
            "sql": """
                INSERT INTO empresas (cnpj, razao_social, nome_fantasia, atividade_principal) 
                VALUES ('12345678000195', 'Empresa Teste LTDA', 'Teste Corp', '4712100') 
                ON CONFLICT (cnpj) DO NOTHING;
            """
        },
        {
            "description": "Inserindo produto teste",
            "sql": """
                INSERT INTO produtos (empresa_id, codigo_produto, nome, descricao, categoria) 
                VALUES (1, 'PROD001', 'Smartphone Samsung Galaxy', 'Celular Android 128GB', 'Eletrônicos')
                ON CONFLICT DO NOTHING;
            """
        }
    ]
    
    success_count = 0
    for data in test_data:
        if run_docker_command(data["sql"], data["description"]):
            success_count += 1
        time.sleep(1)
    
    return success_count == len(test_data)

def main():
    """Função principal de configuração"""
    print("🏗️ CONFIGURAÇÃO ROBUSTA DO BANCO DE DADOS")
    print("=" * 50)
    
    # Verificar se container está rodando
    try:
        result = subprocess.run(
            "docker ps --filter name=auditoria_postgresql --format table",
            shell=True,
            capture_output=True,
            text=True
        )
        
        if "auditoria_postgresql" not in result.stdout:
            print("❌ Container PostgreSQL não está rodando!")
            print("💡 Execute: docker-compose up -d")
            sys.exit(1)
            
    except Exception as e:
        print(f"💥 Erro ao verificar container: {e}")
        sys.exit(1)
    
    print("✅ Container PostgreSQL encontrado!")
    
    # Aguardar inicialização completa
    print("⏳ Aguardando inicialização completa do PostgreSQL...")
    time.sleep(5)
    
    # Testar conectividade básica
    if not run_docker_command("SELECT version();", "Testando conectividade"):
        print("❌ Falha na conectividade básica!")
        sys.exit(1)
    
    # Criar tabelas
    print("\n📋 CRIANDO ESTRUTURA DO BANCO")
    print("-" * 30)
    
    if create_basic_tables():
        print("✅ Todas as tabelas foram criadas com sucesso!")
    else:
        print("⚠️ Algumas tabelas podem ter falhado!")
    
    # Inserir dados de teste
    print("\n📝 INSERINDO DADOS DE TESTE")
    print("-" * 30)
    
    if insert_test_data():
        print("✅ Dados de teste inseridos com sucesso!")
    else:
        print("⚠️ Alguns dados de teste podem ter falhado!")
    
    # Verificar resultado final
    print("\n📊 VERIFICAÇÃO FINAL")
    print("-" * 20)
    
    run_docker_command("\\dt", "Listando tabelas criadas")
    run_docker_command("SELECT COUNT(*) as total_usuarios FROM usuarios;", "Contando usuários")
    run_docker_command("SELECT COUNT(*) as total_empresas FROM empresas;", "Contando empresas")
    run_docker_command("SELECT COUNT(*) as total_produtos FROM produtos;", "Contando produtos")
    
    print("\n🎉 CONFIGURAÇÃO CONCLUÍDA!")
    print("✅ Banco de dados PostgreSQL configurado e pronto para uso!")

if __name__ == "__main__":
    main()
