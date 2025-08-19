#!/usr/bin/env python3
"""
Processador de Dados Farmacêuticos
Processa a Tabela ABC Farma com medicamentos para o sistema de auditoria fiscal
"""
import pandas as pd
import json
import logging
from typing import Dict, List, Optional
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FarmaceuticoProcessor:
    """Processador para dados de medicamentos da Tabela ABC Farma"""
    
    def __init__(self, file_path: str = "data/raw/Tabela_ABC_Farma.xlsx"):
        self.file_path = file_path
        self.medicamentos = {}
        self.ncm_farmaceutico = set()
        self.cest_farmaceutico = set()
        
    def carregar_dados(self) -> bool:
        """
        Carrega dados da Tabela ABC Farma
        
        Returns:
            bool: True se carregamento foi bem-sucedido
        """
        try:
            logger.info(f"Carregando dados farmacêuticos de: {self.file_path}")
            
            # Verificar se arquivo existe
            if not Path(self.file_path).exists():
                logger.error(f"Arquivo não encontrado: {self.file_path}")
                return False
            
            # Ler dados
            df = pd.read_excel(self.file_path, sheet_name='Medicamentos')
            logger.info(f"Carregados {len(df)} medicamentos")
            
            # Processar dados
            self._processar_medicamentos(df)
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao carregar dados farmacêuticos: {e}")
            return False
    
    def _processar_medicamentos(self, df: pd.DataFrame):
        """
        Processa dados de medicamentos
        
        Args:
            df: DataFrame com dados de medicamentos
        """
        for _, row in df.iterrows():
            codigo_barras = str(row['codigo_barras'])
            
            medicamento = {
                'codigo_barras': codigo_barras,
                'descricao': row['descricao'],
                'ncm': row['ncm'],
                'cest': row['cest'],
                'principio_ativo': row['principio_ativo'],
                'concentracao': row['concentracao'],
                'forma_farmaceutica': row['forma_farmaceutica'],
                'laboratorio': row['laboratorio'],
                'registro_anvisa': str(row['registro_anvisa']),
                'segmento': 'Medicamentos',
                'capitulo_ncm': '30',  # Capítulo 30 - Produtos Farmacêuticos
                'segmento_cest': '13'  # Segmento 13 - Medicamentos
            }
            
            # Adicionar descrição enriquecida
            medicamento['descricao_enriquecida'] = self._criar_descricao_enriquecida(medicamento)
            
            # Armazenar por código de barras
            self.medicamentos[codigo_barras] = medicamento
            
            # Coletar NCMs e CESTs únicos
            self.ncm_farmaceutico.add(row['ncm'])
            self.cest_farmaceutico.add(row['cest'])
    
    def _criar_descricao_enriquecida(self, medicamento: Dict) -> str:
        """
        Cria descrição enriquecida para melhor classificação
        
        Args:
            medicamento: Dados do medicamento
            
        Returns:
            str: Descrição enriquecida
        """
        descricao_base = medicamento['descricao']
        principio = medicamento['principio_ativo']
        concentracao = medicamento['concentracao']
        forma = medicamento['forma_farmaceutica']
        laboratorio = medicamento['laboratorio']
        
        # Criar descrição enriquecida
        descricao_enriquecida = f"{descricao_base}. "
        descricao_enriquecida += f"Medicamento farmacêutico do capítulo 30 NCM. "
        descricao_enriquecida += f"Princípio ativo: {principio}. "
        descricao_enriquecida += f"Concentração: {concentracao}. "
        descricao_enriquecida += f"Forma farmacêutica: {forma}. "
        descricao_enriquecida += f"Laboratório: {laboratorio}. "
        descricao_enriquecida += f"Produto sujeito à substituição tributária (CEST segmento 13)."
        
        return descricao_enriquecida
    
    def buscar_por_codigo_barras(self, codigo_barras: str) -> Optional[Dict]:
        """
        Busca medicamento por código de barras
        
        Args:
            codigo_barras: Código de barras do produto
            
        Returns:
            Dict ou None: Dados do medicamento se encontrado
        """
        return self.medicamentos.get(codigo_barras)
    
    def buscar_por_ncm(self, ncm: str) -> List[Dict]:
        """
        Busca medicamentos por NCM
        
        Args:
            ncm: Código NCM
            
        Returns:
            List[Dict]: Lista de medicamentos com o NCM
        """
        return [med for med in self.medicamentos.values() if med['ncm'] == ncm]
    
    def buscar_por_cest(self, cest: str) -> List[Dict]:
        """
        Busca medicamentos por CEST
        
        Args:
            cest: Código CEST
            
        Returns:
            List[Dict]: Lista de medicamentos com o CEST
        """
        return [med for med in self.medicamentos.values() if med['cest'] == cest]
    
    def buscar_por_principio_ativo(self, principio: str) -> List[Dict]:
        """
        Busca medicamentos por princípio ativo
        
        Args:
            principio: Princípio ativo
            
        Returns:
            List[Dict]: Lista de medicamentos com o princípio ativo
        """
        principio_lower = principio.lower()
        return [
            med for med in self.medicamentos.values() 
            if principio_lower in med['principio_ativo'].lower()
        ]
    
    def buscar_similares(self, descricao: str, limite: int = 5) -> List[Dict]:
        """
        Busca medicamentos similares por descrição
        
        Args:
            descricao: Descrição para busca
            limite: Número máximo de resultados
            
        Returns:
            List[Dict]: Lista de medicamentos similares
        """
        descricao_lower = descricao.lower()
        medicamentos_similares = []
        
        for medicamento in self.medicamentos.values():
            # Verificar similaridade na descrição
            desc_med = medicamento['descricao'].lower()
            principio_med = medicamento['principio_ativo'].lower()
            
            score = 0
            # Pontuação por palavras em comum na descrição
            palavras_desc = set(descricao_lower.split())
            palavras_med = set(desc_med.split())
            palavras_principio = set(principio_med.split())
            
            score += len(palavras_desc.intersection(palavras_med)) * 2
            score += len(palavras_desc.intersection(palavras_principio)) * 3
            
            if score > 0:
                medicamento_com_score = medicamento.copy()
                medicamento_com_score['similarity_score'] = score
                medicamentos_similares.append(medicamento_com_score)
        
        # Ordenar por score e retornar top resultados
        medicamentos_similares.sort(key=lambda x: x['similarity_score'], reverse=True)
        return medicamentos_similares[:limite]
    
    def get_estatisticas(self) -> Dict:
        """
        Retorna estatísticas dos dados farmacêuticos
        
        Returns:
            Dict: Estatísticas dos dados
        """
        return {
            'total_medicamentos': len(self.medicamentos),
            'ncms_unicos': len(self.ncm_farmaceutico),
            'cests_unicos': len(self.cest_farmaceutico),
            'ncms': list(self.ncm_farmaceutico),
            'cests': list(self.cest_farmaceutico),
            'laboratorios': list(set(med['laboratorio'] for med in self.medicamentos.values())),
            'formas_farmaceuticas': list(set(med['forma_farmaceutica'] for med in self.medicamentos.values())),
            'principios_ativos': list(set(med['principio_ativo'] for med in self.medicamentos.values()))
        }
    
    def exportar_para_json(self, output_path: str = "data/processed/medicamentos_abc_farma.json"):
        """
        Exporta dados processados para JSON
        
        Args:
            output_path: Caminho do arquivo de saída
        """
        try:
            # Criar diretório se não existir
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            dados_export = {
                'medicamentos': self.medicamentos,
                'estatisticas': self.get_estatisticas(),
                'metadados': {
                    'fonte': self.file_path,
                    'tipo': 'Medicamentos ABC Farma',
                    'total_registros': len(self.medicamentos)
                }
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(dados_export, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Dados exportados para: {output_path}")
            
        except Exception as e:
            logger.error(f"Erro ao exportar dados: {e}")

def main():
    """Função principal para teste do processador"""
    processor = FarmaceuticoProcessor()
    
    if processor.carregar_dados():
        # Mostrar estatísticas
        stats = processor.get_estatisticas()
        print("📊 Estatísticas dos Medicamentos ABC Farma:")
        print(f"   Total de medicamentos: {stats['total_medicamentos']}")
        print(f"   NCMs únicos: {stats['ncms_unicos']}")
        print(f"   CESTs únicos: {stats['cests_unicos']}")
        print(f"   Laboratórios: {len(stats['laboratorios'])}")
        print(f"   Formas farmacêuticas: {len(stats['formas_farmaceuticas'])}")
        
        # Exportar dados
        processor.exportar_para_json()
        
        # Teste de busca
        print("\n🔍 Teste de busca por 'DIPIRONA':")
        similares = processor.buscar_similares("DIPIRONA")
        for med in similares[:3]:
            print(f"   {med['descricao']} - Score: {med['similarity_score']}")

if __name__ == "__main__":
    main()
