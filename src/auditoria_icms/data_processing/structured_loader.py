"""
Structured Data Loader para Sistema de Auditoria Fiscal ICMS v16.0
Responsável pela ingestão, limpeza e normalização de dados estruturados
Inclui integração com Tabela ABC Farma e processador NESH
"""

import pandas as pd
import json
import re
import os
from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path

# Imports dos novos processadores
try:
    from .farmaceutico_processor import FarmaceuticoProcessor
    from .nesh_processor import NESHProcessor
except ImportError:
    # Fallback para execução direta
    import sys
    sys.path.append(os.path.dirname(__file__))
    try:
        from farmaceutico_processor import FarmaceuticoProcessor
        from nesh_processor import NESHProcessor
    except ImportError:
        logger.warning("Processadores farmacêutico e NESH não disponíveis")

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StructuredDataLoader:
    """Classe principal para carregamento de dados estruturados"""
    
    def __init__(self, data_dir: str = None):
        self.data_dir = data_dir or "./data/raw"
        
        # Inicializa novos processadores se disponíveis
        try:
            self.farmaceutico_processor = FarmaceuticoProcessor()
            self.nesh_processor = NESHProcessor(data_path=self.data_dir)
            self.processadores_disponíveis = True
        except NameError:
            self.farmaceutico_processor = None
            self.nesh_processor = None
            self.processadores_disponíveis = False
            logger.warning("Processadores farmacêutico e NESH não disponíveis")
        
        # Cache para dados carregados
        self._farma_data = None
        self._nesh_rules = None
        
    @staticmethod
    def clean_ncm_code(code) -> str:
        """Remove a pontuação de um código NCM e garante a consistência."""
        if pd.isna(code) or code is None:
            return ""
        if not isinstance(code, str):
            code = str(code)
        cleaned_code = re.sub(r'[^0-9]', '', code)
        return cleaned_code.ljust(8, '0')[:8]
    
    @staticmethod
    def clean_cest_code(code) -> str:
        """Remove a pontuação de um código CEST e garante a consistência."""
        if pd.isna(code) or code is None:
            return ""
        if not isinstance(code, str):
            code = str(code)
        cleaned_code = re.sub(r'[^0-9]', '', code)
        return cleaned_code.ljust(9, '0')[:9]
    
    @staticmethod
    def get_ncm_hierarchy(code: str) -> Dict[str, str]:
        """Extrai a hierarquia de um código NCM de 8 dígitos."""
        code = StructuredDataLoader.clean_ncm_code(code)
        return {
            'capitulo': code[:2],
            'posicao': code[:4],
            'subposicao': code[:6]
        }
    
    def process_ncm_data(self) -> pd.DataFrame:
        """Processa a tabela NCM principal."""
        logger.info("Processando dados NCM...")
        
        # Lista arquivos disponíveis no diretório
        if os.path.exists(self.data_dir):
            files = os.listdir(self.data_dir)
            logger.info(f"Arquivos encontrados: {files}")
        else:
            logger.warning(f"Diretório {self.data_dir} não encontrado")
            return pd.DataFrame()
        
        # Tenta diferentes formatos de arquivo
        ncm_file_paths = [
            os.path.join(self.data_dir, 'Tabela_NCM.xlsx'),
            os.path.join(self.data_dir, 'tabela_ncm.xlsx')
        ]
        
        ncm_df = None
        for file_path in ncm_file_paths:
            if os.path.exists(file_path):
                try:
                    ncm_df = pd.read_excel(file_path, dtype={'Código': str})
                    logger.info(f"Arquivo NCM carregado: {file_path}")
                    break
                except Exception as e:
                    logger.error(f"Erro ao carregar {file_path}: {e}")
        
        if ncm_df is None:
            logger.warning("Arquivo de tabela NCM não encontrado, criando DataFrame vazio")
            return pd.DataFrame(columns=['codigo', 'descricao', 'capitulo', 'posicao', 'subposicao'])
        
        # Normaliza nomes das colunas
        column_mapping = {
            'Código': 'codigo',
            'Código NCM': 'codigo',
            'Descrição': 'descricao',
            'Descrição NCM': 'descricao',
            'Description': 'descricao'
        }
        
        for old_col, new_col in column_mapping.items():
            if old_col in ncm_df.columns:
                ncm_df.rename(columns={old_col: new_col}, inplace=True)
        
        # Filtra apenas códigos NCM completos (8 dígitos)
        if 'codigo' in ncm_df.columns:
            ncm_df['codigo_limpo'] = ncm_df['codigo'].apply(self.clean_ncm_code)
            ncm_df = ncm_df[ncm_df['codigo_limpo'].str.len() == 8].copy()
            
            # Extrai hierarquia
            hierarchy_data = ncm_df['codigo_limpo'].apply(self.get_ncm_hierarchy)
            hierarchy_df = pd.DataFrame(hierarchy_data.tolist())
            
            # Combina dados
            ncm_final = pd.concat([ncm_df.reset_index(drop=True), hierarchy_df], axis=1)
            ncm_final = ncm_final[['codigo_limpo', 'descricao', 'capitulo', 'posicao', 'subposicao']]
            ncm_final.rename(columns={'codigo_limpo': 'codigo'}, inplace=True)
            
            # Remove duplicatas
            ncm_final = ncm_final.drop_duplicates(subset=['codigo'])
            
            logger.info(f"Processados {len(ncm_final)} códigos NCM")
            return ncm_final
        else:
            logger.warning("Coluna 'codigo' não encontrada no arquivo NCM")
            return pd.DataFrame(columns=['codigo', 'descricao', 'capitulo', 'posicao', 'subposicao'])
    
    def load_medicamentos_abc_farma(self) -> Dict:
        """
        Carrega dados de medicamentos da Tabela ABC Farma
        
        Returns:
            Dict: Dados de medicamentos processados
        """
        if not self.processadores_disponíveis or not self.farmaceutico_processor:
            logger.warning("Processador farmacêutico não disponível")
            return {}
        
        if self._farma_data is None:
            logger.info("Carregando dados de medicamentos ABC Farma...")
            if self.farmaceutico_processor.carregar_dados():
                self._farma_data = {
                    'medicamentos': self.farmaceutico_processor.medicamentos,
                    'ncm_farmaceutico': list(self.farmaceutico_processor.ncm_farmaceutico),
                    'cest_farmaceutico': list(self.farmaceutico_processor.cest_farmaceutico),
                    'estatisticas': self.farmaceutico_processor.get_estatisticas()
                }
                logger.info(f"Carregados {len(self._farma_data['medicamentos'])} medicamentos")
            else:
                self._farma_data = {}
        
        return self._farma_data
    
    def load_nesh_rules(self) -> Dict:
        """
        Carrega regras e notas explicativas do NESH
        
        Returns:
            Dict: Regras e notas do NESH processadas
        """
        if not self.processadores_disponíveis or not self.nesh_processor:
            logger.warning("Processador NESH não disponível")
            return {}
        
        if self._nesh_rules is None:
            logger.info("Carregando regras NESH...")
            nesh_data = self.nesh_processor.load_nesh_pdf()
            if nesh_data:
                self._nesh_rules = nesh_data
                logger.info(f"Carregadas {len(nesh_data.get('regras_gerais', {}))} regras gerais")
            else:
                self._nesh_rules = {}
        
        return self._nesh_rules
    
    def buscar_medicamento_por_codigo_barras(self, codigo_barras: str) -> Optional[Dict]:
        """
        Busca medicamento por código de barras
        
        Args:
            codigo_barras: Código de barras do medicamento
            
        Returns:
            Dict ou None: Dados do medicamento se encontrado
        """
        if self.farmaceutico_processor:
            return self.farmaceutico_processor.buscar_por_codigo_barras(codigo_barras)
        return None
    
    def buscar_medicamentos_similares(self, descricao: str, limite: int = 5) -> List[Dict]:
        """
        Busca medicamentos similares por descrição
        
        Args:
            descricao: Descrição para busca
            limite: Número máximo de resultados
            
        Returns:
            List[Dict]: Lista de medicamentos similares
        """
        if self.farmaceutico_processor:
            return self.farmaceutico_processor.buscar_similares(descricao, limite)
        return []
    
    def get_regra_ncm(self, numero_regra: str) -> Optional[Dict]:
        """
        Busca regra geral de interpretação NCM
        
        Args:
            numero_regra: Número da regra (ex: "1", "2A", "RGC1")
            
        Returns:
            Dict ou None: Dados da regra se encontrada
        """
        nesh_data = self.load_nesh_rules()
        return nesh_data.get('regras_gerais', {}).get(numero_regra)
    
    def validar_ncm_com_nesh(self, ncm: str, descricao: str = "") -> Dict:
        """
        Valida código NCM usando regras NESH
        
        Args:
            ncm: Código NCM para validar
            descricao: Descrição do produto (opcional)
            
        Returns:
            Dict: Resultado da validação
        """
        if self.nesh_processor:
            return self.nesh_processor.validate_ncm(ncm, descricao)
        return {"valido": False, "observacoes": ["Processador NESH não disponível"]}
    
    def run_simple_test(self):
        """Executa um teste simples do loader."""
        logger.info("=== Teste Simples do StructuredDataLoader ===")
        
        # Testa processamento NCM
        ncm_df = self.process_ncm_data()
        logger.info(f"Teste NCM: {len(ncm_df)} registros processados")
        
        # Testa novos processadores
        if self.processadores_disponíveis:
            # Teste medicamentos
            farma_data = self.load_medicamentos_abc_farma()
            if farma_data:
                logger.info(f"Teste ABC Farma: {len(farma_data.get('medicamentos', {}))} medicamentos")
            
            # Teste NESH
            nesh_data = self.load_nesh_rules()
            if nesh_data:
                logger.info(f"Teste NESH: {len(nesh_data.get('regras_gerais', {}))} regras gerais")
        
        # Lista arquivos disponíveis
        if os.path.exists(self.data_dir):
            files = os.listdir(self.data_dir)
            logger.info(f"Arquivos no diretório {self.data_dir}: {files}")
        else:
            logger.warning(f"Diretório {self.data_dir} não existe")
        
        logger.info("=== Teste Concluído ===")
        return True

def main():
    """Função principal para teste."""
    loader = StructuredDataLoader()
    loader.run_simple_test()

if __name__ == "__main__":
    main()
