# Database Models for Auditoria Fiscal ICMS v15.0
"""
Modelos SQLAlchemy para o sistema de auditoria fiscal v15.0
Implementa estrutura multi-tenant com auditoria completa e Golden Set
"""

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, Date, 
    ForeignKey, Numeric, JSON, Index, UniqueConstraint, Float
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from datetime import datetime
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

Base = declarative_base()

# =============================================================================
# BANCO DA APLICAÇÃO (Multiempresa) - ATUALIZADO FASE 2
# =============================================================================

class Usuario(Base):
    """Modelo para usuários do sistema"""
    __tablename__ = 'usuarios'
    
    id = Column(Integer, primary_key=True)
    nome = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    cargo = Column(String(100))
    identificacao = Column(String(50))
    senha_hash = Column(String(255), nullable=False)
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime, default=func.now())
    
    # Relacionamentos
    acessos_empresa = relationship("UsuarioEmpresaAcesso", back_populates="usuario")
    
    # Relacionamentos
    acessos_empresa = relationship("UsuarioEmpresaAcesso", back_populates="usuario")

class Empresa(Base):
    __tablename__ = 'empresas'
    
    id = Column(Integer, primary_key=True)
    nome = Column(String(255), nullable=False)
    cnpj = Column(String(14), unique=True, nullable=False)
    uf = Column(String(2), nullable=False)
    segmento_fiscal = Column(String(100))
    # Novos campos para Fase 2
    atividades = Column(Text, nullable=False)
    endereco = Column(Text)
    contador = Column(String(255))
    socios = Column(Text)
    dados_sintegra = Column(JSON)
    # Configurações de conexão com banco da empresa
    db_config = Column(JSON)  # Configurações de conexão externa
    ativa = Column(Boolean, default=True)
    criada_em = Column(DateTime, default=func.now())
    
    # Relacionamentos
    usuarios_acesso = relationship("UsuarioEmpresaAcesso", back_populates="empresa")
    mercadorias = relationship("MercadoriaClassificar", back_populates="empresa")
    agregacoes = relationship("Agregacao", back_populates="empresa")
    logs_auditoria = relationship("AuditoriaAgentesLog", back_populates="empresa")

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
    codigo_produto = Column(String(100))
    codigo_barra = Column(String(100))
    ncm_correto = Column(String(8), nullable=False)
    cest_correto = Column(String(9))
    justificativa_ncm = Column(Text, nullable=False)
    justificativa_cest = Column(Text)
    fonte_usuario = Column(String(255))
    fonte_empresa = Column(String(255))
    validado_por = Column(String(255))
    data_confirmacao = Column(DateTime, default=func.now())
    confiabilidade = Column(String(20), default='alta')  # alta, media, baixa
    categoria = Column(String(100))
    tags = Column(JSON)
    observacoes = Column(Text)
    ativo = Column(Boolean, default=True)
    
    __table_args__ = (
        Index('idx_golden_set_ncm_cest', 'ncm_correto', 'cest_correto'),
        Index('idx_golden_set_gtin', 'gtin'),
        Index('idx_golden_set_categoria', 'categoria'),
    )

# Novas tabelas para auditoria - Fase 2
class AuditoriaAgentesLog(Base):
    """Log de auditoria das ações dos agentes"""
    __tablename__ = 'auditoria_agentes_log'
    
    log_id = Column(Integer, primary_key=True)
    empresa_id = Column(Integer, ForeignKey('empresas.id'), nullable=False)
    produto_id_origem = Column(String(100), nullable=False)
    agente_nome = Column(String(100), nullable=False)
    timestamp = Column(DateTime, default=func.now())
    acao_realizada = Column(String(255), nullable=False)
    dados_entrada = Column(JSON)
    dados_saida = Column(JSON)
    justificativa_rag = Column(Text)
    query_rag = Column(Text)
    contexto_rag = Column(JSON)
    confianca = Column(Float)
    status = Column(String(50), default='sucesso')  # sucesso, erro, pendente
    tempo_execucao = Column(Float)  # em segundos
    erro_detalhes = Column(Text)
    
    # Relacionamentos
    empresa = relationship("Empresa", back_populates="logs_auditoria")
    
    __table_args__ = (
        Index('idx_auditoria_empresa_agente', 'empresa_id', 'agente_nome'),
        Index('idx_auditoria_timestamp', 'timestamp'),
        Index('idx_auditoria_produto', 'produto_id_origem'),
    )

class ConfiguracaoProcessamento(Base):
    """Configurações de processamento por empresa"""
    __tablename__ = 'configuracao_processamento'
    
    id = Column(Integer, primary_key=True)
    empresa_id = Column(Integer, ForeignKey('empresas.id'), nullable=False)
    batch_size = Column(Integer, default=100)
    enable_enrichment = Column(Boolean, default=True)
    enable_ncm_classification = Column(Boolean, default=True)
    enable_cest_classification = Column(Boolean, default=True)
    enable_reconciliation = Column(Boolean, default=True)
    confianca_minima = Column(Float, default=0.7)
    auto_approve_threshold = Column(Float, default=0.9)
    configuracoes_agentes = Column(JSON)
    timeout_agente = Column(Integer, default=300)  # segundos
    max_retries = Column(Integer, default=3)
    data_criacao = Column(DateTime, default=func.now())
    data_atualizacao = Column(DateTime, default=func.now())
    
    __table_args__ = (
        Index('idx_config_empresa', 'empresa_id'),
    )

class StatusProcessamento(Base):
    """Status do processamento em lote por empresa"""
    __tablename__ = 'status_processamento'
    
    id = Column(Integer, primary_key=True)
    empresa_id = Column(Integer, ForeignKey('empresas.id'), nullable=False)
    task_id = Column(String(100), unique=True, nullable=False)
    total_produtos = Column(Integer, nullable=False)
    produtos_processados = Column(Integer, default=0)
    produtos_com_erro = Column(Integer, default=0)
    status = Column(String(50), default='iniciado')  # iniciado, em_progresso, concluido, erro, cancelado
    data_inicio = Column(DateTime, default=func.now())
    data_conclusao = Column(DateTime)
    tempo_estimado = Column(Integer)  # segundos
    detalhes_progresso = Column(JSON)
    configuracao_usada = Column(JSON)
    
    __table_args__ = (
        Index('idx_status_empresa_task', 'empresa_id', 'task_id'),
        Index('idx_status_data_inicio', 'data_inicio'),
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


class ProdutoEmpresa(Base):
    """
    Representa um produto no banco de dados da empresa externa
    Usado para mapear produtos extraídos dos sistemas das empresas
    """
    __tablename__ = 'produtos_empresa'
    
    produto_id = Column(String(100), primary_key=True, comment="ID único do produto na empresa")
    empresa_id = Column(Integer, ForeignKey('empresas.id'), nullable=False, comment="ID da empresa no sistema")
    codigo_produto = Column(String(50), nullable=False, comment="Código do produto na empresa")
    descricao_produto = Column(Text, nullable=False, comment="Descrição original do produto")
    codigo_barra = Column(String(20), nullable=True, comment="Código de barras do produto")
    
    # Classificações originais da empresa
    ncm = Column(String(8), nullable=True, comment="NCM original informado pela empresa")
    cest = Column(String(10), nullable=True, comment="CEST original informado pela empresa")
    
    # Resultados do processamento dos agentes
    descricao_enriquecida = Column(Text, nullable=True, comment="Descrição enriquecida pelos agentes")
    ncm_sugerido = Column(String(8), nullable=True, comment="NCM sugerido pelos agentes")
    cest_sugerido = Column(String(10), nullable=True, comment="CEST sugerido pelos agentes")
    
    # Métricas de confiança
    confianca_ncm = Column(Float, nullable=True, comment="Confiança da classificação NCM (0.0 a 1.0)")
    confianca_cest = Column(Float, nullable=True, comment="Confiança da classificação CEST (0.0 a 1.0)")
    
    # Justificativas dos agentes
    justificativa_ncm = Column(Text, nullable=True, comment="Justificativa da classificação NCM")
    justificativa_cest = Column(Text, nullable=True, comment="Justificativa da classificação CEST")
    
    # Status do processamento
    status_processamento = Column(String(20), nullable=True, default='PENDENTE', 
                                comment="Status: PENDENTE, PROCESSADO, ERRO, REVISAO_PENDENTE")
    revisao_manual = Column(Boolean, default=False, comment="Indica se requer revisão manual")
    
    # Campos de controle
    data_criacao = Column(DateTime, default=func.now, comment="Data de criação do registro")
    data_atualizacao = Column(DateTime, default=func.now, onupdate=func.now, comment="Data de última atualização")
    data_processamento = Column(DateTime, nullable=True, comment="Data do último processamento pelos agentes")
    
    # Relacionamento com empresa
    empresa = relationship("Empresa", back_populates="produtos")
    
    def __repr__(self):
        return f"<ProdutoEmpresa(produto_id='{self.produto_id}', codigo='{self.codigo_produto}', empresa_id={self.empresa_id})>"
    
    def to_dict(self):
        """Converte o objeto para dicionário"""
        return {
            'produto_id': self.produto_id,
            'empresa_id': self.empresa_id,
            'codigo_produto': self.codigo_produto,
            'descricao_produto': self.descricao_produto,
            'codigo_barra': self.codigo_barra,
            'ncm': self.ncm,
            'cest': self.cest,
            'descricao_enriquecida': self.descricao_enriquecida,
            'ncm_sugerido': self.ncm_sugerido,
            'cest_sugerido': self.cest_sugerido,
            'confianca_ncm': self.confianca_ncm,
            'confianca_cest': self.confianca_cest,
            'justificativa_ncm': self.justificativa_ncm,
            'justificativa_cest': self.justificativa_cest,
            'status_processamento': self.status_processamento,
            'revisao_manual': self.revisao_manual,
            'data_criacao': self.data_criacao.isoformat() if self.data_criacao else None,
            'data_atualizacao': self.data_atualizacao.isoformat() if self.data_atualizacao else None,
            'data_processamento': self.data_processamento.isoformat() if self.data_processamento else None
        }


# Atualiza o relacionamento na classe Empresa
Empresa.produtos = relationship("ProdutoEmpresa", back_populates="empresa")
