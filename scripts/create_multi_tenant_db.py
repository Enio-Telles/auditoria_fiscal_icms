"""
Script para criar arquitetura multi-tenant com bancos separados
- auditoria_central: Banco principal com empresas e usuários
- golden_set: Banco para verdades fundamentais (compartilhado)
- empresa_[cnpj]: Banco específico para cada empresa
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import re
import os
from sqlalchemy import create_engine, text, MetaData, Table, Column, Integer, String, DateTime, Boolean, Text, Numeric, ForeignKey
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

# Configurações de conexão
DB_HOST = "localhost"
DB_PORT = "5432"
DB_USER = "postgres"
DB_PASSWORD = "postgres123"

Base = declarative_base()

def sanitize_cnpj_for_db_name(cnpj):
    """Sanitiza CNPJ para usar como nome de banco"""
    # Remove caracteres especiais e mantém apenas números
    cnpj_clean = re.sub(r'[^0-9]', '', cnpj)
    return f"empresa_{cnpj_clean}"

def create_database_if_not_exists(db_name):
    """Cria banco de dados se não existir"""
    try:
        # Conectar ao PostgreSQL sem especificar banco
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database="postgres"
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        
        cursor = conn.cursor()
        
        # Verificar se banco existe
        cursor.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s", (db_name,))
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute(f'CREATE DATABASE "{db_name}"')
            print(f"✅ Banco '{db_name}' criado com sucesso!")
        else:
            print(f"ℹ️  Banco '{db_name}' já existe")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar banco '{db_name}': {e}")
        return False

def get_engine(db_name):
    """Cria engine SQLAlchemy para um banco específico"""
    db_url = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{db_name}"
    return create_engine(db_url, echo=True)

# =================== MODELOS DO BANCO CENTRAL ===================

class Usuario(Base):
    __tablename__ = 'usuarios'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    senha_hash = Column(String(255), nullable=False)
    nome_completo = Column(String(100))
    ativo = Column(Boolean, default=True)
    admin = Column(Boolean, default=False)
    criado_em = Column(DateTime, default=datetime.utcnow)
    ultimo_login = Column(DateTime)

class Empresa(Base):
    __tablename__ = 'empresas'
    
    id = Column(Integer, primary_key=True)
    cnpj = Column(String(18), unique=True, nullable=False)
    razao_social = Column(String(200), nullable=False)
    nome_fantasia = Column(String(200))
    endereco = Column(Text)
    cidade = Column(String(100))
    estado = Column(String(2))
    cep = Column(String(10))
    telefone = Column(String(20))
    email = Column(String(100))
    atividade_principal = Column(String(10))  # CNAE
    regime_tributario = Column(String(20))  # Simples, Presumido, Real
    database_name = Column(String(100), nullable=False)  # Nome do banco específico
    ativa = Column(Boolean, default=True)
    criada_em = Column(DateTime, default=datetime.utcnow)
    atualizada_em = Column(DateTime, default=datetime.utcnow)

class PermissaoEmpresa(Base):
    __tablename__ = 'permissoes_empresa'
    
    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'))
    empresa_id = Column(Integer, ForeignKey('empresas.id'))
    nivel_acesso = Column(String(20))  # admin, auditor, consulta
    criada_em = Column(DateTime, default=datetime.utcnow)

# =================== MODELOS DO GOLDEN SET ===================

class GoldenSetNCM(Base):
    __tablename__ = 'golden_set_ncm'
    
    id = Column(Integer, primary_key=True)
    produto_nome = Column(Text, nullable=False)
    produto_descricao = Column(Text)
    categoria = Column(String(100))
    marca = Column(String(100))
    ncm_codigo = Column(String(10), nullable=False)
    ncm_descricao = Column(Text)
    confianca = Column(Numeric(5,2), default=100.0)
    fonte = Column(String(100))  # Manual, Importacao, etc
    validado_por = Column(String(100))
    validado_em = Column(DateTime)
    criado_em = Column(DateTime, default=datetime.utcnow)
    ativo = Column(Boolean, default=True)

class GoldenSetCEST(Base):
    __tablename__ = 'golden_set_cest'
    
    id = Column(Integer, primary_key=True)
    ncm_codigo = Column(String(10), nullable=False)
    cest_codigo = Column(String(7), nullable=False)
    cest_descricao = Column(Text)
    estado = Column(String(2))  # Para regras estaduais específicas
    atividade_cnae = Column(String(10))  # CNAE da empresa
    confianca = Column(Numeric(5,2), default=100.0)
    fonte = Column(String(100))
    validado_por = Column(String(100))
    validado_em = Column(DateTime)
    criado_em = Column(DateTime, default=datetime.utcnow)
    ativo = Column(Boolean, default=True)

# =================== MODELOS POR EMPRESA ===================

def create_empresa_models():
    """Define modelos para bancos de empresa"""
    
    class Produto(Base):
        __tablename__ = 'produtos'
        
        id = Column(Integer, primary_key=True)
        codigo_interno = Column(String(50))
        ean = Column(String(20))
        nome = Column(Text, nullable=False)
        descricao = Column(Text)
        categoria = Column(String(100))
        subcategoria = Column(String(100))
        marca = Column(String(100))
        modelo = Column(String(100))
        unidade = Column(String(10))
        preco_custo = Column(Numeric(12,2))
        preco_venda = Column(Numeric(12,2))
        estoque_atual = Column(Integer)
        ncm_codigo = Column(String(10))
        cest_codigo = Column(String(7))
        origem = Column(String(1))  # 0=Nacional, 1=Importado, etc
        cst_icms = Column(String(3))
        aliquota_icms = Column(Numeric(5,2))
        ativo = Column(Boolean, default=True)
        criado_em = Column(DateTime, default=datetime.utcnow)
        atualizado_em = Column(DateTime, default=datetime.utcnow)
    
    class ClassificacaoIA(Base):
        __tablename__ = 'classificacoes_ia'
        
        id = Column(Integer, primary_key=True)
        produto_id = Column(Integer, ForeignKey('produtos.id'))
        ncm_sugerido = Column(String(10))
        ncm_confianca = Column(Numeric(5,2))
        cest_sugerido = Column(String(7))
        cest_confianca = Column(Numeric(5,2))
        justificativa = Column(Text)
        agente_usado = Column(String(50))
        status = Column(String(20))  # pendente, aprovado, rejeitado
        processado_em = Column(DateTime, default=datetime.utcnow)
        aprovado_por = Column(String(100))
        aprovado_em = Column(DateTime)
    
    class AuditoriaClassificacao(Base):
        __tablename__ = 'auditoria_classificacoes'
        
        id = Column(Integer, primary_key=True)
        produto_id = Column(Integer, ForeignKey('produtos.id'))
        ncm_anterior = Column(String(10))
        ncm_novo = Column(String(10))
        cest_anterior = Column(String(7))
        cest_novo = Column(String(7))
        motivo_alteracao = Column(Text)
        usuario = Column(String(100))
        alterado_em = Column(DateTime, default=datetime.utcnow)
    
    return Produto, ClassificacaoIA, AuditoriaClassificacao

def setup_central_database():
    """Configura banco central com empresas e usuários"""
    print("\n🏢 Configurando banco CENTRAL...")
    
    if not create_database_if_not_exists("auditoria_central"):
        return False
    
    try:
        engine = get_engine("auditoria_central")
        Base.metadata.create_all(engine, tables=[
            Usuario.__table__,
            Empresa.__table__,
            PermissaoEmpresa.__table__
        ])
        
        print("✅ Banco central configurado com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao configurar banco central: {e}")
        return False

def setup_golden_set_database():
    """Configura banco do Golden Set"""
    print("\n🏆 Configurando banco GOLDEN SET...")
    
    if not create_database_if_not_exists("golden_set"):
        return False
    
    try:
        engine = get_engine("golden_set")
        Base.metadata.create_all(engine, tables=[
            GoldenSetNCM.__table__,
            GoldenSetCEST.__table__
        ])
        
        print("✅ Banco Golden Set configurado com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao configurar Golden Set: {e}")
        return False

def create_empresa_database(cnpj, razao_social):
    """Cria banco específico para uma empresa"""
    db_name = sanitize_cnpj_for_db_name(cnpj)
    
    print(f"\n🏭 Criando banco para empresa: {razao_social}")
    print(f"   CNPJ: {cnpj}")
    print(f"   Banco: {db_name}")
    
    if not create_database_if_not_exists(db_name):
        return None
    
    try:
        # Criar modelos específicos da empresa
        Produto, ClassificacaoIA, AuditoriaClassificacao = create_empresa_models()
        
        engine = get_engine(db_name)
        Base.metadata.create_all(engine, tables=[
            Produto.__table__,
            ClassificacaoIA.__table__,
            AuditoriaClassificacao.__table__
        ])
        
        print(f"✅ Banco da empresa criado: {db_name}")
        return db_name
        
    except Exception as e:
        print(f"❌ Erro ao criar banco da empresa: {e}")
        return None

def register_empresa_in_central(cnpj, razao_social, database_name, **kwargs):
    """Registra empresa no banco central"""
    try:
        engine = get_engine("auditoria_central")
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Verificar se empresa já existe
        empresa_existente = session.query(Empresa).filter_by(cnpj=cnpj).first()
        
        if empresa_existente:
            print(f"ℹ️  Empresa {cnpj} já registrada")
            session.close()
            return empresa_existente.id
        
        # Criar nova empresa
        nova_empresa = Empresa(
            cnpj=cnpj,
            razao_social=razao_social,
            database_name=database_name,
            **kwargs
        )
        
        session.add(nova_empresa)
        session.commit()
        
        empresa_id = nova_empresa.id
        session.close()
        
        print(f"✅ Empresa registrada no banco central: ID {empresa_id}")
        return empresa_id
        
    except Exception as e:
        print(f"❌ Erro ao registrar empresa: {e}")
        return None

def create_default_user():
    """Cria usuário administrador padrão"""
    try:
        engine = get_engine("auditoria_central")
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Verificar se usuário admin já existe
        admin_existente = session.query(Usuario).filter_by(username='admin').first()
        
        if admin_existente:
            print("ℹ️  Usuário admin já existe")
            session.close()
            return
        
        # Criar usuário admin
        admin_user = Usuario(
            username='admin',
            email='admin@auditoria.com',
            senha_hash='admin123',  # Em produção, usar hash real
            nome_completo='Administrador do Sistema',
            admin=True
        )
        
        session.add(admin_user)
        session.commit()
        session.close()
        
        print("✅ Usuário admin criado: username=admin, senha=admin123")
        
    except Exception as e:
        print(f"❌ Erro ao criar usuário admin: {e}")

def setup_sample_companies():
    """Cria empresas de exemplo"""
    empresas_exemplo = [
        {
            'cnpj': '12.345.678/0001-90',
            'razao_social': 'ABC Farmácia Ltda',
            'nome_fantasia': 'Farmácia ABC',
            'atividade_principal': '4771700',  # Comércio varejista de produtos farmacêuticos
            'regime_tributario': 'Simples Nacional'
        },
        {
            'cnpj': '98.765.432/0001-10',
            'razao_social': 'Tech Solutions Informática Ltda',
            'nome_fantasia': 'Tech Solutions',
            'atividade_principal': '4751200',  # Comércio varejista de equipamentos de informática
            'regime_tributario': 'Lucro Presumido'
        },
        {
            'cnpj': '11.222.333/0001-44',
            'razao_social': 'SuperMercado Central Ltda',
            'nome_fantasia': 'SuperMercado Central',
            'atividade_principal': '4711301',  # Comércio varejista de mercadorias em geral
            'regime_tributario': 'Lucro Real'
        }
    ]
    
    print("\n🏪 Criando empresas de exemplo...")
    
    for empresa_data in empresas_exemplo:
        cnpj = empresa_data['cnpj']
        razao_social = empresa_data['razao_social']
        
        # Criar banco da empresa
        db_name = create_empresa_database(cnpj, razao_social)
        
        if db_name:
            # Registrar no banco central
            empresa_data['database_name'] = db_name
            empresa_id = register_empresa_in_central(**empresa_data)
            
            if empresa_id:
                print(f"✅ Empresa completa: {razao_social} (ID: {empresa_id})")

def main():
    """Execução principal"""
    print("🚀 CONFIGURAÇÃO MULTI-TENANT - AUDITORIA FISCAL ICMS")
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
    create_default_user()
    
    # 4. Criar empresas de exemplo
    setup_sample_companies()
    
    print("\n" + "=" * 60)
    print("🎉 CONFIGURAÇÃO MULTI-TENANT CONCLUÍDA!")
    print("\n📊 Bancos criados:")
    print("   • auditoria_central - Usuários e empresas")
    print("   • golden_set - Verdades fundamentais")
    print("   • empresa_12345678000190 - ABC Farmácia")
    print("   • empresa_98765432000110 - Tech Solutions")
    print("   • empresa_11222333000144 - SuperMercado Central")
    print("\n🔐 Acesso:")
    print("   • Usuário: admin")
    print("   • Senha: admin123")
    print("   • Host: localhost:5432")

if __name__ == "__main__":
    main()
