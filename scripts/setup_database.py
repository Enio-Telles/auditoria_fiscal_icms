"""
Script de inicialização do banco de dados PostgreSQL
para o Sistema de Auditoria Fiscal ICMS v15.0
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from src.auditoria_icms.database.models import Base
import os
from dotenv import load_dotenv

load_dotenv()

# Configurações do banco
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:postgres123@localhost:5432/auditoria_fiscal"
)


def create_database_engine():
    """Cria a engine do banco de dados"""
    engine = create_engine(DATABASE_URL, echo=True)
    return engine


def create_tables(engine):
    """Cria todas as tabelas definidas nos modelos"""
    print("Criando tabelas no banco de dados...")
    Base.metadata.create_all(bind=engine)
    print("Tabelas criadas com sucesso!")


def create_indexes(engine):
    """Cria índices adicionais para performance"""
    additional_indexes = [
        # Índices compostos para queries frequentes
        """
        CREATE INDEX IF NOT EXISTS idx_mercadoria_empresa_criado
        ON mercadorias_a_classificar(empresa_id, criado_em DESC);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_classificacao_confianca
        ON classificacoes(confianca_ncm DESC, confianca_cest DESC);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_golden_set_descricao_trgm
        ON golden_set USING gin(descricao_produto gin_trgm_ops);
        """,
        # Índice para busca textual em descrições NCM
        """
        CREATE INDEX IF NOT EXISTS idx_ncm_descricao_trgm
        ON ncm USING gin(descricao gin_trgm_ops);
        """,
    ]

    with engine.connect() as conn:
        # Ativa extensão pg_trgm para busca textual
        try:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm;"))
            conn.commit()
            print("Extensão pg_trgm ativada.")
        except Exception as e:
            print(f"Aviso: Não foi possível ativar pg_trgm: {e}")

        # Cria índices adicionais
        for index_sql in additional_indexes:
            try:
                conn.execute(text(index_sql))
                conn.commit()
                print(f"Índice criado: {index_sql.split()[5]}")
            except Exception as e:
                print(f"Aviso: Erro ao criar índice: {e}")


def insert_initial_data(engine):
    """Insere dados iniciais necessários"""
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Insere segmentos iniciais se não existirem
        from src.auditoria_icms.database.models import Segmento

        segmentos_iniciais = [
            {"codigo": "01", "descricao": "COMBUSTÍVEIS E LUBRIFICANTES"},
            {"codigo": "02", "descricao": "ENERGIA ELÉTRICA"},
            {"codigo": "03", "descricao": "TELECOMUNICAÇÕES"},
            {"codigo": "04", "descricao": "TRANSPORTE"},
            {"codigo": "05", "descricao": "PRODUTOS ALIMENTÍCIOS"},
            {"codigo": "06", "descricao": "BEBIDAS"},
            {"codigo": "07", "descricao": "PRODUTOS FARMACÊUTICOS"},
            {"codigo": "28", "descricao": "MATERIAIS DE CONSTRUÇÃO E CONGÊNERES"},
        ]

        for seg_data in segmentos_iniciais:
            existing = (
                session.query(Segmento).filter_by(codigo=seg_data["codigo"]).first()
            )
            if not existing:
                segmento = Segmento(**seg_data)
                session.add(segmento)

        session.commit()
        print("Dados iniciais inseridos com sucesso!")

    except Exception as e:
        session.rollback()
        print(f"Erro ao inserir dados iniciais: {e}")
    finally:
        session.close()


def setup_database():
    """Função principal para configurar o banco completo"""
    print("=== Configuração do Banco de Dados ===")

    # Cria engine
    engine = create_database_engine()

    # Testa conexão
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print(f"Conectado ao PostgreSQL: {version}")
    except Exception as e:
        print(f"Erro ao conectar com o banco: {e}")
        return False

    # Cria tabelas
    create_tables(engine)

    # Cria índices
    create_indexes(engine)

    # Insere dados iniciais
    insert_initial_data(engine)

    print("=== Configuração concluída! ===")
    return True


if __name__ == "__main__":
    success = setup_database()
    if success:
        print("Banco de dados configurado com sucesso!")
    else:
        print("Falha na configuração do banco de dados!")
        exit(1)
