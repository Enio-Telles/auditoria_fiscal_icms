"""
Structured Data Loader para Sistema de Auditoria Fiscal ICMS v15.0
Responsável pela ingestão, limpeza e normalização de dados estruturados
"""

import pandas as pd
import json
import re
import os
from typing import Dict, List, Optional, Tuple
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StructuredDataLoader:
    """Classe principal para carregamento de dados estruturados"""
    
    def __init__(self, data_dir: str = None):
        self.data_dir = data_dir or "./data/raw"
        
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
    
    def run_simple_test(self):
        """Executa um teste simples do loader."""
        logger.info("=== Teste Simples do StructuredDataLoader ===")
        
        # Testa processamento NCM
        ncm_df = self.process_ncm_data()
        logger.info(f"Teste NCM: {len(ncm_df)} registros processados")
        
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
