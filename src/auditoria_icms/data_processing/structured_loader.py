"""
Estruturador de Dados - Structured Loader
Implementa o carregamento e processamento de todas as fontes de dados estruturados
conforme especificado no Plano de Implementação Fase 1.
"""

import pandas as pd
import json
import sqlite3
import re
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from sqlalchemy import create_engine, text
from datetime import datetime


class StructuredDataLoader:
    """
    Carregador responsável por processar todas as fontes de dados estruturados
    e criar a base de conhecimento relacional em SQLite.
    """
    
    def __init__(self, data_path: str = "data/raw", db_path: str = "data/processed/knowledge_base.sqlite"):
        self.data_path = Path(data_path)
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        
        # Garantir que diretórios existam
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.data_path.mkdir(parents=True, exist_ok=True)
        
    def create_knowledge_base(self) -> bool:
        """
        Função principal para criar a base de conhecimento completa.
        
        Returns:
            True se sucesso, False caso contrário
        """
        try:
            self.logger.info("Iniciando criação da base de conhecimento...")
            
            # Criar engine SQLite
            engine = create_engine(f'sqlite:///{self.db_path}')
            
            # 1. Processar Tabela NCM
            self._process_ncm_data(engine)
            
            # 2. Processar dados CEST
            self._process_cest_data(engine)
            
            # 3. Processar produtos exemplo
            self._process_example_products(engine)
            
            # 4. Criar índices para otimização
            self._create_indexes(engine)
            
            # 5. Validar dados carregados
            self._validate_loaded_data(engine)
            
            self.logger.info("Base de conhecimento criada com sucesso!")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na criação da base de conhecimento: {str(e)}")
            return False
    
    def _process_ncm_data(self, engine):
        """Processa e carrega dados da Tabela NCM."""
        self.logger.info("Processando Tabela NCM...")
        
        try:
            # Tentar diferentes formatos de arquivo NCM
            ncm_files = [
                "Tabela_NCM.xlsx",
                "Tabela NCM.csv", 
                "descricoes_ncm.json",
                "tabela_ncm.csv"
            ]
            
            ncm_df = None
            
            for filename in ncm_files:
                file_path = self.data_path / filename
                if file_path.exists():
                    if filename.endswith('.xlsx'):
                        ncm_df = pd.read_excel(file_path, dtype={'Código': str})
                    elif filename.endswith('.csv'):
                        ncm_df = pd.read_csv(file_path, dtype={'Código': str})
                    elif filename.endswith('.json'):
                        with open(file_path, 'r', encoding='utf-8') as f:
                            ncm_data = json.load(f)
                        ncm_df = pd.DataFrame(ncm_data)
                    break
            
            if ncm_df is None:
                self.logger.warning("Nenhum arquivo NCM encontrado. Criando tabela vazia.")
                self._create_empty_ncm_table(engine)
                return
            
            # Normalizar nomes de colunas
            column_mapping = {
                'Código': 'ncm_codigo',
                'codigo': 'ncm_codigo',
                'Descrição': 'descricao',
                'descricao': 'descricao',
                'Description': 'descricao'
            }
            
            for old_name, new_name in column_mapping.items():
                if old_name in ncm_df.columns:
                    ncm_df.rename(columns={old_name: new_name}, inplace=True)
            
            # Filtrar apenas NCMs completos (8 dígitos)
            if 'ncm_codigo' in ncm_df.columns:
                # Limpar códigos NCM
                ncm_df['ncm_codigo'] = ncm_df['ncm_codigo'].astype(str)
                ncm_df['codigo_limpo'] = ncm_df['ncm_codigo'].apply(self._clean_ncm_code)
                
                # Filtrar NCMs de 8 dígitos
                ncm_full_df = ncm_df[ncm_df['codigo_limpo'].str.len() == 8].copy()
                
                if len(ncm_full_df) == 0:
                    self.logger.warning("Nenhum NCM de 8 dígitos encontrado")
                    self._create_empty_ncm_table(engine)
                    return
                
                # Extrair hierarquia
                hierarchy_data = ncm_full_df['codigo_limpo'].apply(self._get_ncm_hierarchy).tolist()
                hierarchy_df = pd.DataFrame(hierarchy_data)
                
                # Combinar dados
                ncm_final_df = pd.concat([
                    ncm_full_df[['codigo_limpo', 'descricao']].reset_index(drop=True),
                    hierarchy_df
                ], axis=1)
                
                ncm_final_df.rename(columns={'codigo_limpo': 'codigo'}, inplace=True)
                
                # Salvar no banco
                ncm_final_df.to_sql('ncm', engine, if_exists='replace', index=False)
                self.logger.info(f"Tabela 'ncm' criada com {len(ncm_final_df)} registros")
            
        except Exception as e:
            self.logger.error(f"Erro ao processar dados NCM: {str(e)}")
            self._create_empty_ncm_table(engine)
    
    def _process_cest_data(self, engine):
        """Processa e carrega dados CEST."""
        self.logger.info("Processando dados CEST...")
        
        try:
            # Processar Convênio 142
            conv142_data = self._load_convenio_142()
            
            # Processar CEST Rondônia
            cest_ro_data = self._load_cest_rondonia()
            
            # Combinar dados
            all_cest_data = []
            
            if conv142_data:
                all_cest_data.extend(conv142_data)
            
            if cest_ro_data:
                all_cest_data.extend(cest_ro_data)
            
            if not all_cest_data:
                self.logger.warning("Nenhum dado CEST encontrado. Criando tabelas vazias.")
                self._create_empty_cest_tables(engine)
                return
            
            # Criar DataFrames
            cest_df = pd.DataFrame(all_cest_data)
            
            # Processar segmentos
            segmentos_df = cest_df[['segmento_descricao']].drop_duplicates().reset_index(drop=True)
            segmentos_df['id'] = segmentos_df.index + 1
            segmentos_df.to_sql('segmentos', engine, if_exists='replace', index=False)
            
            # Processar regras CEST
            cest_df = cest_df.merge(segmentos_df, on='segmento_descricao', how='left')
            
            # Tabela de regras CEST
            cest_regras_df = cest_df[[
                'cest', 'descricao', 'id', 'situacao', 'vigencia_inicio', 'vigencia_fim'
            ]].drop_duplicates(subset=['cest'])
            cest_regras_df.rename(columns={'id': 'segmento_id'}, inplace=True)
            cest_regras_df.to_sql('cest_regras', engine, if_exists='replace', index=False)
            
            # Tabela de associações NCM-CEST
            ncm_cest_list = []
            for _, row in cest_df.iterrows():
                ncms = self._normalize_cest_ncm_column(row.get('ncm', ''))
                for ncm_pattern in ncms:
                    if ncm_pattern:
                        ncm_cest_list.append({
                            'cest_codigo': row['cest'],
                            'ncm_pattern': ncm_pattern
                        })
            
            if ncm_cest_list:
                ncm_cest_df = pd.DataFrame(ncm_cest_list).drop_duplicates()
                ncm_cest_df.to_sql('ncm_cest_associacao', engine, if_exists='replace', index=False)
            
            self.logger.info(f"Tabelas CEST criadas com {len(cest_regras_df)} regras")
            
        except Exception as e:
            self.logger.error(f"Erro ao processar dados CEST: {str(e)}")
            self._create_empty_cest_tables(engine)
    
    def _process_example_products(self, engine):
        """Processa produtos exemplo."""
        self.logger.info("Processando produtos exemplo...")
        
        try:
            example_files = [
                "produtos_selecionados.json",
                "Tabela_ABC_Farma.xlsx",
                "produtos_exemplo.csv"
            ]
            
            all_products = []
            
            for filename in example_files:
                file_path = self.data_path / filename
                if file_path.exists():
                    if filename.endswith('.json'):
                        with open(file_path, 'r', encoding='utf-8') as f:
                            products = json.load(f)
                        if isinstance(products, list):
                            all_products.extend(products)
                        else:
                            all_products.append(products)
                    
                    elif filename.endswith('.xlsx'):
                        df = pd.read_excel(file_path)
                        products = df.to_dict('records')
                        all_products.extend(products)
                    
                    elif filename.endswith('.csv'):
                        df = pd.read_csv(file_path)
                        products = df.to_dict('records')
                        all_products.extend(products)
            
            if all_products:
                produtos_df = pd.DataFrame(all_products)
                
                # Normalizar colunas
                column_mapping = {
                    'gtin': 'gtin',
                    'codigo_barras': 'gtin',
                    'ean': 'gtin',
                    'descricao': 'descricao',
                    'produto': 'descricao',
                    'nome': 'descricao',
                    'ncm': 'ncm',
                    'cest': 'cest'
                }
                
                for old_name, new_name in column_mapping.items():
                    if old_name in produtos_df.columns and new_name not in produtos_df.columns:
                        produtos_df.rename(columns={old_name: new_name}, inplace=True)
                
                # Limpar códigos
                if 'ncm' in produtos_df.columns:
                    produtos_df['ncm'] = produtos_df['ncm'].apply(self._clean_ncm_code)
                
                if 'cest' in produtos_df.columns:
                    produtos_df['cest'] = produtos_df['cest'].apply(self._clean_ncm_code)
                
                # Filtrar colunas necessárias
                required_columns = ['gtin', 'descricao', 'ncm', 'cest']
                available_columns = [col for col in required_columns if col in produtos_df.columns]
                
                if available_columns:
                    produtos_final_df = produtos_df[available_columns].dropna(subset=['descricao'])
                    produtos_final_df.to_sql('produtos_exemplos', engine, if_exists='replace', index=False)
                    self.logger.info(f"Tabela 'produtos_exemplos' criada com {len(produtos_final_df)} registros")
                
        except Exception as e:
            self.logger.error(f"Erro ao processar produtos exemplo: {str(e)}")
    
    def _load_convenio_142(self) -> List[Dict[str, Any]]:
        """Carrega dados do Convênio 142."""
        file_path = self.data_path / "conv_142_formatado.json"
        
        if not file_path.exists():
            self.logger.warning("Arquivo conv_142_formatado.json não encontrado")
            return []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            processed_data = []
            for item in data:
                processed_data.append({
                    'cest': item.get('CEST', ''),
                    'descricao': item.get('descricao_oficial_cest', ''),
                    'ncm': item.get('NCM', ''),
                    'segmento_descricao': item.get('Anexo', ''),
                    'situacao': 'vigente',
                    'vigencia_inicio': None,
                    'vigencia_fim': None,
                    'fonte': 'Convenio_142'
                })
            
            return processed_data
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar Convênio 142: {str(e)}")
            return []
    
    def _load_cest_rondonia(self) -> List[Dict[str, Any]]:
        """Carrega dados CEST de Rondônia."""
        file_path = self.data_path / "CEST_RO.xlsx"
        
        if not file_path.exists():
            self.logger.warning("Arquivo CEST_RO.xlsx não encontrado")
            return []
        
        try:
            df = pd.read_excel(file_path, dtype=str)
            
            # Normalizar nomes de colunas
            column_mapping = {
                'CEST': 'cest',
                'NCM/SH': 'ncm',
                'DESCRIÇÃO': 'descricao',
                'Situação': 'situacao',
                'Início vig.': 'vigencia_inicio',
                'Fim vig.': 'vigencia_fim',
                'TABELA': 'segmento_descricao'
            }
            
            for old_name, new_name in column_mapping.items():
                if old_name in df.columns:
                    df.rename(columns={old_name: new_name}, inplace=True)
            
            # Filtrar apenas vigentes
            if 'situacao' in df.columns:
                df = df[df['situacao'].str.lower() == 'vigente']
            
            df['fonte'] = 'CEST_RO'
            
            return df.to_dict('records')
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar CEST RO: {str(e)}")
            return []
    
    def _clean_ncm_code(self, code) -> str:
        """Limpa código NCM removendo pontuação."""
        if pd.isna(code) or code is None:
            return ""
        
        code_str = str(code)
        cleaned = re.sub(r'[^0-9]', '', code_str)
        return cleaned.zfill(8) if len(cleaned) <= 8 else cleaned[:8]
    
    def _get_ncm_hierarchy(self, code: str) -> Dict[str, str]:
        """Extrai hierarquia NCM."""
        code = str(code).zfill(8)
        return {
            'capitulo': code[:2],
            'posicao': code[:4],
            'subposicao': code[:6]
        }
    
    def _normalize_cest_ncm_column(self, ncm_string: str) -> List[str]:
        """Normaliza coluna NCM dos arquivos CEST."""
        if pd.isna(ncm_string) or not ncm_string:
            return []
        
        # Dividir por vírgulas e pontos e vírgulas
        items = re.split(r'[,;]', str(ncm_string))
        
        # Limpar cada item
        cleaned_items = []
        for item in items:
            cleaned = re.sub(r'[^0-9.]', '', item.strip())
            if cleaned and len(cleaned) >= 2:
                # Remover pontos para padronizar
                cleaned = cleaned.replace('.', '')
                cleaned_items.append(cleaned)
        
        return cleaned_items
    
    def _create_empty_ncm_table(self, engine):
        """Cria tabela NCM vazia."""
        empty_ncm = pd.DataFrame(columns=['codigo', 'descricao', 'capitulo', 'posicao', 'subposicao'])
        empty_ncm.to_sql('ncm', engine, if_exists='replace', index=False)
        self.logger.info("Tabela NCM vazia criada")
    
    def _create_empty_cest_tables(self, engine):
        """Cria tabelas CEST vazias."""
        # Segmentos
        empty_segmentos = pd.DataFrame(columns=['id', 'descricao'])
        empty_segmentos.to_sql('segmentos', engine, if_exists='replace', index=False)
        
        # Regras CEST
        empty_cest = pd.DataFrame(columns=[
            'cest', 'descricao', 'segmento_id', 'situacao', 'vigencia_inicio', 'vigencia_fim'
        ])
        empty_cest.to_sql('cest_regras', engine, if_exists='replace', index=False)
        
        # Associações
        empty_assoc = pd.DataFrame(columns=['cest_codigo', 'ncm_pattern'])
        empty_assoc.to_sql('ncm_cest_associacao', engine, if_exists='replace', index=False)
        
        self.logger.info("Tabelas CEST vazias criadas")
    
    def _create_indexes(self, engine):
        """Cria índices para otimização."""
        try:
            with engine.connect() as conn:
                # Índices para NCM
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_ncm_codigo ON ncm(codigo)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_ncm_capitulo ON ncm(capitulo)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_ncm_posicao ON ncm(posicao)"))
                
                # Índices para CEST
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_cest_codigo ON cest_regras(cest)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_cest_segmento ON cest_regras(segmento_id)"))
                
                # Índices para associações
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_assoc_cest ON ncm_cest_associacao(cest_codigo)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_assoc_ncm ON ncm_cest_associacao(ncm_pattern)"))
                
                conn.commit()
                
            self.logger.info("Índices criados com sucesso")
            
        except Exception as e:
            self.logger.warning(f"Erro ao criar índices: {str(e)}")
    
    def _validate_loaded_data(self, engine):
        """Valida dados carregados."""
        try:
            with engine.connect() as conn:
                # Contar registros
                ncm_count = conn.execute(text("SELECT COUNT(*) FROM ncm")).scalar()
                cest_count = conn.execute(text("SELECT COUNT(*) FROM cest_regras")).scalar()
                assoc_count = conn.execute(text("SELECT COUNT(*) FROM ncm_cest_associacao")).scalar()
                
                self.logger.info(f"Validação: {ncm_count} NCMs, {cest_count} CESTs, {assoc_count} associações")
                
                # Teste de correspondência
                test_query = text("""
                    SELECT COUNT(*) FROM ncm n
                    JOIN ncm_cest_associacao nca ON n.capitulo = nca.ncm_pattern
                    JOIN cest_regras cr ON nca.cest_codigo = cr.cest
                    LIMIT 1
                """)
                
                test_result = conn.execute(test_query).scalar()
                if test_result > 0:
                    self.logger.info("Teste de correspondência NCM-CEST: OK")
                else:
                    self.logger.warning("Teste de correspondência NCM-CEST: Nenhuma correspondência encontrada")
                
        except Exception as e:
            self.logger.error(f"Erro na validação: {str(e)}")


# Função utilitária para execução standalone
def main():
    """Função principal para execução do carregador."""
    logging.basicConfig(level=logging.INFO)
    
    loader = StructuredDataLoader()
    success = loader.create_knowledge_base()
    
    if success:
        print("✅ Base de conhecimento criada com sucesso!")
    else:
        print("❌ Erro na criação da base de conhecimento")


if __name__ == "__main__":
    main()
