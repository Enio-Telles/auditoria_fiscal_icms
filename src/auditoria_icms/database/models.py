# Database Models for Auditoria Fiscal ICMS v15.0
"""
Modelos SQLAlchemy para o sistema de auditoria fiscal.
Inclui tanto o banco da aplicação (multiempresa) quanto a base de conhecimento.
"""

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, Date, 
    ForeignKey, Numeric, JSON, Index, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

# =============================================================================
# BANCO DA APLICAÇÃO (Multiempresa)
# =============================================================================

class Usuario(Base):
    __tablename__ = 'usuarios'
    
    id = Column(Integer, primary_key=True)
    nome = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    senha_hash = Column(String(255), nullable=False)
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime, default=func.now())
    
    # Relacionamentos
    acessos_empresa = relationship("UsuarioEmpresaAcesso", back_populates="usuario")

class Empresa(Base):
    __tablename__ = 'empresas'
    
    id = Column(Integer, primary_key=True)
    nome = Column(String(255), nullable=False)
    cnpj = Column(String(14), unique=True, nullable=False)
    uf = Column(String(2), nullable=False)
    segmento_fiscal = Column(String(100))
    ativa = Column(Boolean, default=True)
    criada_em = Column(DateTime, default=func.now())
    
    # Relacionamentos
    usuarios_acesso = relationship("UsuarioEmpresaAcesso", back_populates="empresa")
    mercadorias = relationship("MercadoriaClassificar", back_populates="empresa")
    agregacoes = relationship("Agregacao", back_populates="empresa")

class UsuarioEmpresaAcesso(Base):
    __tablename__ = 'usuario_empresa_acesso'
    
    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
    empresa_id = Column(Integer, ForeignKey('empresas.id'), nullable=False)
    perfil = Column(String(50), default='usuario')  # admin, auditor, usuario
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime, default=func.now())
    
    # Relacionamentos
    usuario = relationship("Usuario", back_populates="acessos_empresa")
    empresa = relationship("Empresa", back_populates="usuarios_acesso")
    
    __table_args__ = (UniqueConstraint('usuario_id', 'empresa_id'),)

class MercadoriaClassificar(Base):
    __tablename__ = 'mercadorias_a_classificar'
    
    id = Column(Integer, primary_key=True)
    empresa_id = Column(Integer, ForeignKey('empresas.id'), nullable=False)
    produto_id_origem = Column(String(100), nullable=False)
    descricao_original = Column(Text, nullable=False)
    gtin = Column(String(14))
    marca = Column(String(100))
    modelo = Column(String(100))
    ncm_informado = Column(String(8))
    cest_informado = Column(String(9))
    preco_medio = Column(Numeric(10, 2))
    status = Column(String(50), default='pendente')  # pendente, processado, revisado
    criado_em = Column(DateTime, default=func.now())
    processado_em = Column(DateTime)
    
    # Relacionamentos
    empresa = relationship("Empresa", back_populates="mercadorias")
    classificacoes = relationship("Classificacao", back_populates="mercadoria")
    agregacoes = relationship("Agregacao", back_populates="mercadoria")
    
    __table_args__ = (
        Index('idx_mercadoria_empresa_status', 'empresa_id', 'status'),
        Index('idx_mercadoria_ncm', 'ncm_informado'),
    )

class Classificacao(Base):
    __tablename__ = 'classificacoes'
    
    id = Column(Integer, primary_key=True)
    mercadoria_id = Column(Integer, ForeignKey('mercadorias_a_classificar.id'), nullable=False)
    ncm_determinado = Column(String(8), nullable=False)
    cest_determinado = Column(String(9))
    confianca_ncm = Column(Numeric(3, 2))  # 0.00 a 1.00
    confianca_cest = Column(Numeric(3, 2))
    justificativa_ncm = Column(Text)
    contexto_ncm = Column(Text)
    justificativa_cest = Column(Text)
    contexto_cest = Column(Text)
    agente_responsavel = Column(String(100))
    revisado_por_humano = Column(Boolean, default=False)
    aprovado = Column(Boolean)
    observacoes_revisor = Column(Text)
    criado_em = Column(DateTime, default=func.now())
    revisado_em = Column(DateTime)
    
    # Relacionamentos
    mercadoria = relationship("MercadoriaClassificar", back_populates="classificacoes")
    
    __table_args__ = (
        Index('idx_classificacao_ncm_cest', 'ncm_determinado', 'cest_determinado'),
    )

class Agregacao(Base):
    __tablename__ = 'agregacoes'
    
    id = Column(Integer, primary_key=True)
    empresa_id = Column(Integer, ForeignKey('empresas.id'), nullable=False)
    produto_conceitual_id = Column(String(100), nullable=False)
    mercadoria_id = Column(Integer, ForeignKey('mercadorias_a_classificar.id'), nullable=False)
    descricao_conceitual = Column(Text)
    criterio_agregacao = Column(String(100))  # descricao_similar, gtin_similar, etc
    confianca_agregacao = Column(Numeric(3, 2))
    criado_em = Column(DateTime, default=func.now())
    
    # Relacionamentos
    empresa = relationship("Empresa", back_populates="agregacoes")
    mercadoria = relationship("MercadoriaClassificar", back_populates="agregacoes")
    
    __table_args__ = (
        Index('idx_agregacao_empresa_conceitual', 'empresa_id', 'produto_conceitual_id'),
    )

class GoldenSet(Base):
    __tablename__ = 'golden_set'
    
    id = Column(Integer, primary_key=True)
    descricao_produto = Column(Text, nullable=False)
    descricao_enriquecida = Column(Text, nullable=False)
    gtin = Column(String(14))
    ncm_correto = Column(String(8), nullable=False)
    cest_correto = Column(String(9))
    fonte_usuario = Column(String(255))
    fonte_empresa = Column(String(255))
    data_confirmacao = Column(DateTime, default=func.now())
    confiabilidade = Column(String(20), default='alta')  # alta, media, baixa
    categoria = Column(String(100))
    observacoes = Column(Text)
    
    __table_args__ = (
        Index('idx_golden_set_ncm_cest', 'ncm_correto', 'cest_correto'),
        Index('idx_golden_set_gtin', 'gtin'),
    )

# =============================================================================
# BASE DE CONHECIMENTO (Knowledge Base)
# =============================================================================

class NCM(Base):
    __tablename__ = 'ncm'
    
    codigo = Column(String(8), primary_key=True)
    descricao = Column(Text, nullable=False)
    capitulo = Column(String(2), nullable=False)
    posicao = Column(String(4), nullable=False)
    subposicao = Column(String(6), nullable=False)
    unidade_estatistica = Column(String(10))
    aliquota_ipi = Column(Numeric(5, 2))
    criado_em = Column(DateTime, default=func.now())
    
    # Relacionamentos
    cest_associacoes = relationship("NCMCestAssociacao", back_populates="ncm")
    
    __table_args__ = (
        Index('idx_ncm_hierarquia', 'capitulo', 'posicao', 'subposicao'),
    )

class Segmento(Base):
    __tablename__ = 'segmentos'
    
    id = Column(Integer, primary_key=True)
    codigo = Column(String(10), unique=True, nullable=False)
    descricao = Column(Text, nullable=False)
    
    # Relacionamentos
    cest_regras = relationship("CestRegra", back_populates="segmento")

class CestRegra(Base):
    __tablename__ = 'cest_regras'
    
    cest = Column(String(9), primary_key=True)
    descricao = Column(Text, nullable=False)
    segmento_id = Column(Integer, ForeignKey('segmentos.id'), nullable=False)
    situacao = Column(String(50), default='ativo')
    vigencia_inicio = Column(Date)
    vigencia_fim = Column(Date)
    observacoes = Column(Text)
    
    # Relacionamentos
    segmento = relationship("Segmento", back_populates="cest_regras")
    ncm_associacoes = relationship("NCMCestAssociacao", back_populates="cest_regra")
    
    __table_args__ = (
        Index('idx_cest_segmento', 'segmento_id'),
        Index('idx_cest_vigencia', 'vigencia_inicio', 'vigencia_fim'),
    )

class NCMCestAssociacao(Base):
    __tablename__ = 'ncm_cest_associacao'
    
    id = Column(Integer, primary_key=True)
    cest_codigo = Column(String(9), ForeignKey('cest_regras.cest'), nullable=False)
    ncm_pattern = Column(String(8), nullable=False)  # Pode ser padrão como "3004*"
    ncm_codigo_completo = Column(String(8), ForeignKey('ncm.codigo'))  # Para NCM específico
    tipo_associacao = Column(String(20), default='especifico')  # especifico, padrao, hierarquico
    nivel_hierarquia = Column(String(20))  # capitulo, posicao, subposicao, subitem
    
    # Relacionamentos
    cest_regra = relationship("CestRegra", back_populates="ncm_associacoes")
    ncm = relationship("NCM", back_populates="cest_associacoes")
    
    __table_args__ = (
        Index('idx_ncm_cest_pattern', 'ncm_pattern'),
        Index('idx_ncm_cest_completo', 'ncm_codigo_completo'),
    )

class ProdutoExemplo(Base):
    __tablename__ = 'produtos_exemplos'
    
    gtin = Column(String(14), primary_key=True)
    descricao = Column(Text, nullable=False)
    ncm = Column(String(8), nullable=False)
    cest = Column(String(9))
    marca = Column(String(100))
    categoria = Column(String(100))
    fonte = Column(String(100))  # selecionados, anvisa, outros
    confiabilidade = Column(String(20), default='alta')
    
    __table_args__ = (
        Index('idx_produto_ncm_cest', 'ncm', 'cest'),
    )

class NeshNote(Base):
    __tablename__ = 'nesh_notes'
    
    id = Column(Integer, primary_key=True)
    codigo_referencia = Column(String(20))  # Pode referenciar NCM, Capítulo, etc
    tipo_referencia = Column(String(20))  # capitulo, posicao, ncm, geral
    titulo = Column(String(500))
    texto = Column(Text, nullable=False)
    nivel = Column(Integer, default=1)  # Para hierarquia de notas
    origem = Column(String(50))  # NESH, Regras Gerais, etc
    
    __table_args__ = (
        Index('idx_nesh_codigo_tipo', 'codigo_referencia', 'tipo_referencia'),
    )

# =============================================================================
# LOGS E AUDITORIA
# =============================================================================

class LogAgente(Base):
    __tablename__ = 'logs_agentes'
    
    id = Column(Integer, primary_key=True)
    mercadoria_id = Column(Integer, ForeignKey('mercadorias_a_classificar.id'))
    agente_nome = Column(String(100), nullable=False)
    acao = Column(String(100), nullable=False)
    entrada = Column(JSON)
    saida = Column(JSON)
    tempo_execucao = Column(Numeric(8, 3))  # em segundos
    sucesso = Column(Boolean, default=True)
    erro = Column(Text)
    timestamp = Column(DateTime, default=func.now())
    
    __table_args__ = (
        Index('idx_log_agente_timestamp', 'agente_nome', 'timestamp'),
    )
