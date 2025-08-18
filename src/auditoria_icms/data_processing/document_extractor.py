"""
Document Extractor para Sistema de Auditoria Fiscal ICMS v15.0
Responsável pela extração de dados não-estruturados (NESH, Regras Gerais)
"""

import os
import re
import logging
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import json

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DocumentExtractor:
    """Classe para extração de documentos não-estruturados"""
    
    def __init__(self, data_dir: str = None):
        self.data_dir = data_dir or "./data/raw"
        
    def extract_nesh_notes(self) -> List[Dict]:
        """Extrai notas e observações do documento NESH."""
        logger.info("Extraindo notas do documento NESH...")
        
        nesh_file = os.path.join(self.data_dir, 'nesh-2022_REGRAS_GERAIS.docx')
        
        if not os.path.exists(nesh_file):
            logger.warning(f"Arquivo NESH não encontrado: {nesh_file}")
            return []
        
        try:
            # Para esta implementação inicial, vou simular a extração
            # Em produção, usaríamos python-docx para extrair o texto real
            logger.info(f"Arquivo NESH encontrado: {nesh_file}")
            
            # Simulação de notas extraídas
            notas_simuladas = [
                {
                    'id': 1,
                    'codigo_referencia': '30',
                    'tipo_referencia': 'capitulo',
                    'titulo': 'Produtos farmacêuticos',
                    'texto': 'Este Capítulo compreende os produtos farmacêuticos para medicina humana ou veterinária.',
                    'nivel': 1,
                    'origem': 'NESH'
                },
                {
                    'id': 2,
                    'codigo_referencia': '3004',
                    'tipo_referencia': 'posicao',
                    'titulo': 'Medicamentos constituídos por produtos misturados',
                    'texto': 'Medicamentos (exceto os produtos das posições 30.02, 30.05 ou 30.06) constituídos por produtos misturados ou não misturados, preparados para fins terapêuticos ou profiláticos.',
                    'nivel': 2,
                    'origem': 'NESH'
                },
                {
                    'id': 3,
                    'codigo_referencia': 'geral',
                    'tipo_referencia': 'geral',
                    'titulo': 'Regras Gerais para Interpretação',
                    'texto': 'A classificação de mercadorias na Nomenclatura rege-se pelas seguintes Regras: 1) Os títulos das Seções, Capítulos e Subcapítulos têm apenas valor indicativo.',
                    'nivel': 1,
                    'origem': 'Regras_Gerais'
                }
            ]
            
            logger.info(f"Extraídas {len(notas_simuladas)} notas do NESH (simulação)")
            return notas_simuladas
            
        except Exception as e:
            logger.error(f"Erro ao processar arquivo NESH: {e}")
            return []
    
    def extract_with_real_docx(self, file_path: str) -> List[Dict]:
        """Extrai texto real de arquivo DOCX usando python-docx."""
        try:
            from docx import Document
            
            doc = Document(file_path)
            notas = []
            
            for i, paragraph in enumerate(doc.paragraphs):
                text = paragraph.text.strip()
                if text and len(text) > 50:  # Filtra parágrafos significativos
                    # Tenta identificar códigos NCM no texto
                    ncm_matches = re.findall(r'\b\d{2}\.?\d{2}\.?\d{2}\.?\d{2}\b', text)
                    capitulo_matches = re.findall(r'\bCapítulo\s+(\d{1,2})\b', text, re.IGNORECASE)
                    
                    codigo_ref = 'geral'
                    tipo_ref = 'geral'
                    
                    if ncm_matches:
                        codigo_ref = ncm_matches[0].replace('.', '')
                        if len(codigo_ref) == 8:
                            tipo_ref = 'ncm'
                        elif len(codigo_ref) == 6:
                            tipo_ref = 'subposicao'
                        elif len(codigo_ref) == 4:
                            tipo_ref = 'posicao'
                        elif len(codigo_ref) == 2:
                            tipo_ref = 'capitulo'
                    elif capitulo_matches:
                        codigo_ref = capitulo_matches[0].zfill(2)
                        tipo_ref = 'capitulo'
                    
                    notas.append({
                        'id': i + 1,
                        'codigo_referencia': codigo_ref,
                        'tipo_referencia': tipo_ref,
                        'titulo': text[:100] + '...' if len(text) > 100 else text,
                        'texto': text,
                        'nivel': 1,
                        'origem': 'NESH'
                    })
            
            return notas
            
        except ImportError:
            logger.warning("python-docx não está instalado, usando simulação")
            return self.extract_nesh_notes()
        except Exception as e:
            logger.error(f"Erro ao extrair com python-docx: {e}")
            return self.extract_nesh_notes()
    
    def process_all_documents(self) -> Dict[str, List[Dict]]:
        """Processa todos os documentos não-estruturados."""
        logger.info("Processando todos os documentos não-estruturados...")
        
        results = {
            'nesh_notes': [],
            'regras_gerais': [],
            'other_documents': []
        }
        
        # Processa NESH
        nesh_file = os.path.join(self.data_dir, 'nesh-2022_REGRAS_GERAIS.docx')
        if os.path.exists(nesh_file):
            try:
                # Tenta usar python-docx se disponível
                results['nesh_notes'] = self.extract_with_real_docx(nesh_file)
            except:
                # Fallback para simulação
                results['nesh_notes'] = self.extract_nesh_notes()
        
        # Busca outros documentos
        if os.path.exists(self.data_dir):
            for file in os.listdir(self.data_dir):
                if file.endswith(('.pdf', '.docx', '.doc', '.txt')):
                    file_path = os.path.join(self.data_dir, file)
                    logger.info(f"Documento encontrado: {file}")
                    
                    if 'nesh' not in file.lower():
                        results['other_documents'].append({
                            'file_name': file,
                            'file_path': file_path,
                            'file_size': os.path.getsize(file_path),
                            'processed': False
                        })
        
        # Estatísticas
        total_notes = len(results['nesh_notes'])
        total_docs = len(results['other_documents'])
        
        logger.info(f"Processamento concluído:")
        logger.info(f"- NESH notes extraídas: {total_notes}")
        logger.info(f"- Outros documentos encontrados: {total_docs}")
        
        return results
    
    def save_extracted_data(self, data: Dict, output_file: str = None):
        """Salva dados extraídos em arquivo JSON."""
        if output_file is None:
            output_file = os.path.join(self.data_dir, '..', 'processed', 'extracted_documents.json')
        
        # Cria diretório se não existir
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Dados extraídos salvos em: {output_file}")
            
        except Exception as e:
            logger.error(f"Erro ao salvar dados extraídos: {e}")
    
    def run_extraction_test(self):
        """Executa teste de extração de documentos."""
        logger.info("=== Teste de Extração de Documentos ===")
        
        # Lista arquivos disponíveis
        if os.path.exists(self.data_dir):
            files = os.listdir(self.data_dir)
            logger.info(f"Arquivos encontrados: {files}")
        else:
            logger.warning(f"Diretório {self.data_dir} não existe")
            return False
        
        # Processa documentos
        extracted_data = self.process_all_documents()
        
        # Salva resultados
        self.save_extracted_data(extracted_data)
        
        logger.info("=== Teste de Extração Concluído ===")
        return True

def main():
    """Função principal para teste."""
    extractor = DocumentExtractor()
    extractor.run_extraction_test()

if __name__ == "__main__":
    main()
