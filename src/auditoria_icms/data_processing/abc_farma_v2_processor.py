#!/usr/bin/env python3
"""
Processador Avançado ABC Farma V2
Processa a Tabela_ABC_Farma_V2.xlsx com 388k+ medicamentos
Implementa agregação, busca avançada e integração com regras NCM/CEST
"""
import pandas as pd
import json
import logging
import hashlib
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import re
from collections import defaultdict

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ABCFarmaV2Processor:
    """
    Processador avançado para Tabela ABC Farma V2
    Implementa funcionalidades do Plano Fase 2:
    - Agregação de produtos similares (ponto 0.1)
    - Identificação por código de barras
    - Classificação NCM/CEST para medicamentos (ponto 24)
    - Estrutura hierárquica NCM (ponto 21)
    """
    
    def __init__(self, file_path: str = "data/raw/Tabela_ABC_Farma_V2.xlsx"):
        self.file_path = file_path
        self.df_original = None
        self.medicamentos = {}
        self.agregados = {}  # id_agregados -> lista de produtos
        self.ncm_index = defaultdict(list)
        self.cest_index = defaultdict(list)
        self.codigo_barras_index = {}
        self.descricao_index = {}
        
        # Estatísticas
        self.stats = {
            'total_registros': 0,
            'produtos_unicos': 0,
            'grupos_agregados': 0,
            'ncms_unicos': set(),
            'cests_unicos': set(),
            'laboratorios_unicos': set()
        }
    
    def carregar_dados(self, sample_size: Optional[int] = None) -> bool:
        """
        Carrega dados da Tabela ABC Farma V2
        
        Args:
            sample_size: Número de registros para carregar (None = todos)
            
        Returns:
            bool: True se carregamento foi bem-sucedido
        """
        try:
            logger.info(f"Carregando dados de: {self.file_path}")
            
            if not Path(self.file_path).exists():
                logger.error(f"Arquivo não encontrado: {self.file_path}")
                return False
            
            # Ler arquivo Excel
            if sample_size:
                self.df_original = pd.read_excel(self.file_path, nrows=sample_size)
                logger.info(f"Carregando amostra de {sample_size} registros...")
            else:
                self.df_original = pd.read_excel(self.file_path)
            
            logger.info(f"Carregados {len(self.df_original)} registros")
            
            # Processar dados
            return self._processar_dados()
            
        except Exception as e:
            logger.error(f"Erro ao carregar dados: {e}")
            return False
    
    def _processar_dados(self) -> bool:
        """
        Processa e estrutura os dados carregados
        
        Returns:
            bool: True se processamento foi bem-sucedido
        """
        try:
            logger.info("Processando dados ABC Farma V2...")
            
            # Limpar e normalizar dados
            self._limpar_dados()
            
            # Implementar agregação conforme ponto 0.1 do plano
            self._agregar_produtos()
            
            # Criar índices para busca rápida
            self._criar_indices()
            
            # Calcular estatísticas
            self._calcular_estatisticas()
            
            logger.info(f"Processamento concluído: {self.stats['produtos_unicos']} produtos únicos")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao processar dados: {e}")
            return False
    
    def _limpar_dados(self):
        """Limpa e normaliza os dados"""
        
        # Renomear colunas para padrão
        column_mapping = {
            'codigo_barras': 'codigo_barras',
            'descricao': 'descricao', 
            'ncm': 'ncm',
            'cest': 'cest'
        }
        
        # Verificar quais colunas existem
        existing_cols = self.df_original.columns.tolist()
        logger.info(f"Colunas encontradas: {existing_cols}")
        
        # Mapear para colunas padrão se necessário
        if 'codigo_barras' not in existing_cols:
            # Tentar encontrar coluna similar
            barcode_cols = [col for col in existing_cols if 'codigo' in col.lower() or 'barras' in col.lower() or 'gtin' in col.lower()]
            if barcode_cols:
                self.df_original['codigo_barras'] = self.df_original[barcode_cols[0]]
        
        # Remover registros com dados críticos faltantes
        before_count = len(self.df_original)
        self.df_original = self.df_original.dropna(subset=['descricao'])
        
        # Normalizar descrições
        self.df_original['descricao'] = self.df_original['descricao'].str.upper().str.strip()
        
        # Normalizar códigos de barras
        if 'codigo_barras' in self.df_original.columns:
            self.df_original['codigo_barras'] = self.df_original['codigo_barras'].astype(str).str.strip()
        
        # Normalizar NCM
        if 'ncm' in self.df_original.columns:
            self.df_original['ncm'] = self.df_original['ncm'].astype(str).str.replace('.', '').str.strip()
        
        # Normalizar CEST
        if 'cest' in self.df_original.columns:
            self.df_original['cest'] = self.df_original['cest'].astype(str).str.replace('.', '').str.strip()
        
        after_count = len(self.df_original)
        logger.info(f"Limpeza concluída: {before_count} -> {after_count} registros")
    
    def _agregar_produtos(self):
        """
        Implementa agregação de produtos conforme ponto 0.1 do plano:
        - Produtos com descrições iguais são agregados automaticamente
        - Produtos com códigos similares e descrições parecidas são identificados
        """
        logger.info("Implementando agregação de produtos...")
        
        # Criar hash de descrição para agregação automática
        self.df_original['hash_descricao'] = self.df_original['descricao'].apply(
            lambda x: hashlib.md5(x.encode()).hexdigest()[:8]
        )
        
        # Adicionar DENSE_RANK para id_agregados (conforme SQL do plano)
        self.df_original['id_agregados'] = self.df_original['descricao'].rank(method='dense').astype(int)
        
        # Contar produtos por descrição
        desc_counts = self.df_original['descricao'].value_counts()
        self.df_original['qtd_mesma_desc'] = self.df_original['descricao'].map(desc_counts)
        
        # Agrupar por id_agregados
        for id_agregado, grupo in self.df_original.groupby('id_agregados'):
            produtos_grupo = []
            
            for _, row in grupo.iterrows():
                produto = {
                    'codigo_barras': row.get('codigo_barras', ''),
                    'descricao': row['descricao'],
                    'ncm': row.get('ncm', ''),
                    'cest': row.get('cest', ''),
                    'id_agregados': id_agregado,
                    'qtd_mesma_desc': row['qtd_mesma_desc'],
                    'hash_descricao': row['hash_descricao']
                }
                
                # Adicionar campos extras se existirem
                for col in self.df_original.columns:
                    if col not in produto and not pd.isna(row[col]):
                        produto[col] = row[col]
                
                produtos_grupo.append(produto)
                
                # Indexar por código de barras
                if produto['codigo_barras']:
                    self.codigo_barras_index[produto['codigo_barras']] = produto
            
            self.agregados[id_agregado] = produtos_grupo
            
            # Escolher produto representativo (primeiro do grupo)
            produto_principal = produtos_grupo[0]
            produto_principal['produtos_agregados'] = len(produtos_grupo)
            self.medicamentos[id_agregado] = produto_principal
        
        logger.info(f"Agregação concluída: {len(self.agregados)} grupos de produtos")
    
    def _criar_indices(self):
        """Cria índices para busca rápida"""
        
        for id_produto, produto in self.medicamentos.items():
            # Índice por NCM
            if produto['ncm']:
                self.ncm_index[produto['ncm']].append(id_produto)
            
            # Índice por CEST
            if produto['cest']:
                self.cest_index[produto['cest']].append(id_produto)
            
            # Índice por descrição
            palavras = produto['descricao'].split()
            for palavra in palavras:
                if len(palavra) > 3:  # Ignorar palavras muito pequenas
                    if palavra not in self.descricao_index:
                        self.descricao_index[palavra] = []
                    self.descricao_index[palavra].append(id_produto)
    
    def _calcular_estatisticas(self):
        """Calcula estatísticas dos dados processados"""
        
        self.stats['total_registros'] = len(self.df_original)
        self.stats['produtos_unicos'] = len(self.medicamentos)
        self.stats['grupos_agregados'] = len(self.agregados)
        
        for produto in self.medicamentos.values():
            if produto['ncm']:
                self.stats['ncms_unicos'].add(produto['ncm'])
            if produto['cest']:
                self.stats['cests_unicos'].add(produto['cest'])
            
            # Tentar identificar laboratório
            if 'laboratorio' in produto:
                self.stats['laboratorios_unicos'].add(produto['laboratorio'])
    
    def buscar_por_codigo_barras(self, codigo_barras: str) -> Optional[Dict]:
        """
        Busca medicamento por código de barras
        
        Args:
            codigo_barras: Código de barras do produto
            
        Returns:
            Dict ou None: Dados do medicamento se encontrado
        """
        return self.codigo_barras_index.get(codigo_barras)
    
    def buscar_por_ncm(self, ncm: str) -> List[Dict]:
        """
        Busca medicamentos por NCM
        
        Args:
            ncm: Código NCM
            
        Returns:
            List[Dict]: Lista de medicamentos com o NCM
        """
        ncm_limpo = ncm.replace('.', '').strip()
        ids_produtos = self.ncm_index.get(ncm_limpo, [])
        return [self.medicamentos[id_prod] for id_prod in ids_produtos]
    
    def buscar_por_cest(self, cest: str) -> List[Dict]:
        """
        Busca medicamentos por CEST
        
        Args:
            cest: Código CEST
            
        Returns:
            List[Dict]: Lista de medicamentos com o CEST
        """
        cest_limpo = cest.replace('.', '').strip()
        ids_produtos = self.cest_index.get(cest_limpo, [])
        return [self.medicamentos[id_prod] for id_prod in ids_produtos]
    
    def buscar_similares(self, descricao: str, limite: int = 10) -> List[Dict]:
        """
        Busca medicamentos similares por descrição
        Implementa busca inteligente conforme ponto 0.1 do plano
        
        Args:
            descricao: Descrição para busca
            limite: Número máximo de resultados
            
        Returns:
            List[Dict]: Lista de medicamentos similares ordenados por relevância
        """
        descricao_normalizada = descricao.upper().strip()
        palavras_busca = set(descricao_normalizada.split())
        
        # Busca exata primeiro
        for produto in self.medicamentos.values():
            if produto['descricao'] == descricao_normalizada:
                return [produto]
        
        # Busca por similaridade
        scores = {}
        
        for palavra in palavras_busca:
            if palavra in self.descricao_index:
                for id_produto in self.descricao_index[palavra]:
                    if id_produto not in scores:
                        scores[id_produto] = 0
                    scores[id_produto] += 1
        
        # Ordenar por score e calcular similaridade mais detalhada
        resultados = []
        for id_produto, score_palavras in scores.items():
            produto = self.medicamentos[id_produto]
            
            # Calcular score detalhado
            palavras_produto = set(produto['descricao'].split())
            intersecao = len(palavras_busca.intersection(palavras_produto))
            uniao = len(palavras_busca.union(palavras_produto))
            
            similarity_score = (intersecao / uniao) * 100 if uniao > 0 else 0
            
            produto_com_score = produto.copy()
            produto_com_score['similarity_score'] = similarity_score
            produto_com_score['palavras_matching'] = intersecao
            
            resultados.append(produto_com_score)
        
        # Ordenar por similaridade e retornar top resultados
        resultados.sort(key=lambda x: x['similarity_score'], reverse=True)
        return resultados[:limite]
    
    def agregar_produtos_iguais(self, threshold: float = 0.85) -> Dict:
        """
        Identifica e agrega produtos que são iguais mas têm descrições diferentes
        Implementa ponto 0.1 do plano
        
        Args:
            threshold: Limite de similaridade para considerar produtos iguais
            
        Returns:
            Dict: Relatório de agregação
        """
        logger.info(f"Identificando produtos iguais com threshold {threshold}")
        
        produtos_para_agregar = []
        produtos_processados = set()
        
        for id1, produto1 in self.medicamentos.items():
            if id1 in produtos_processados:
                continue
            
            grupo_similar = [produto1]
            produtos_processados.add(id1)
            
            for id2, produto2 in self.medicamentos.items():
                if id2 in produtos_processados or id2 == id1:
                    continue
                
                # Verificar se têm códigos similares (mesmo código de produto)
                codigo_similar = False
                if 'codigo_produto' in produto1 and 'codigo_produto' in produto2:
                    codigo_similar = produto1['codigo_produto'] == produto2['codigo_produto']
                
                # Calcular similaridade de descrição
                desc1_palavras = set(produto1['descricao'].split())
                desc2_palavras = set(produto2['descricao'].split())
                
                intersecao = len(desc1_palavras.intersection(desc2_palavras))
                uniao = len(desc1_palavras.union(desc2_palavras))
                similaridade = intersecao / uniao if uniao > 0 else 0
                
                # Critérios para agregação (ponto 0.1 do plano)
                deve_agregar = False
                
                if codigo_similar and similaridade >= threshold * 0.8:
                    deve_agregar = True  # Código igual + descrição similar
                elif similaridade >= threshold:
                    deve_agregar = True  # Descrição muito similar
                
                if deve_agregar:
                    grupo_similar.append(produto2)
                    produtos_processados.add(id2)
            
            if len(grupo_similar) > 1:
                produtos_para_agregar.append(grupo_similar)
        
        # Gerar relatório
        relatorio = {
            'grupos_encontrados': len(produtos_para_agregar),
            'produtos_afetados': sum(len(grupo) for grupo in produtos_para_agregar),
            'detalhes_grupos': []
        }
        
        for i, grupo in enumerate(produtos_para_agregar):
            detalhes_grupo = {
                'grupo_id': i + 1,
                'produtos_no_grupo': len(grupo),
                'descricoes': [p['descricao'] for p in grupo],
                'ncms': list(set(p['ncm'] for p in grupo if p['ncm'])),
                'cests': list(set(p['cest'] for p in grupo if p['cest'])),
                'codigos_barras': [p['codigo_barras'] for p in grupo if p['codigo_barras']]
            }
            relatorio['detalhes_grupos'].append(detalhes_grupo)
        
        logger.info(f"Encontrados {relatorio['grupos_encontrados']} grupos para agregação")
        return relatorio
    
    def validar_ncm_cest_consistency(self) -> Dict:
        """
        Valida consistência entre NCM e CEST nos medicamentos
        Conforme pontos 21 e 22 do plano
        
        Returns:
            Dict: Relatório de validação
        """
        logger.info("Validando consistência NCM/CEST...")
        
        inconsistencias = []
        ncm_cest_mapping = defaultdict(set)
        
        for produto in self.medicamentos.values():
            ncm = produto.get('ncm', '')
            cest = produto.get('cest', '')
            
            if ncm and cest:
                ncm_cest_mapping[ncm].add(cest)
                
                # Validar capítulo 30 (medicamentos)
                if not ncm.startswith('30'):
                    inconsistencias.append({
                        'tipo': 'NCM_INVALIDO_CAPITULO',
                        'produto': produto['descricao'],
                        'ncm': ncm,
                        'problema': 'NCM não pertence ao capítulo 30 (medicamentos)'
                    })
                
                # Validar segmento 13 CEST (medicamentos)
                if not cest.startswith('13'):
                    inconsistencias.append({
                        'tipo': 'CEST_INVALIDO_SEGMENTO',
                        'produto': produto['descricao'],
                        'cest': cest,
                        'problema': 'CEST não pertence ao segmento 13 (medicamentos)'
                    })
        
        # Identificar NCMs com múltiplos CESTs
        ncm_multiplos_cest = {ncm: cests for ncm, cests in ncm_cest_mapping.items() if len(cests) > 1}
        
        relatorio = {
            'total_produtos': len(self.medicamentos),
            'inconsistencias': len(inconsistencias),
            'detalhes_inconsistencias': inconsistencias,
            'ncm_multiplos_cest': dict(ncm_multiplos_cest),
            'resumo_ncm_cest': {ncm: list(cests) for ncm, cests in ncm_cest_mapping.items()}
        }
        
        logger.info(f"Validação concluída: {len(inconsistencias)} inconsistências encontradas")
        return relatorio
    
    def get_estatisticas_detalhadas(self) -> Dict:
        """
        Retorna estatísticas detalhadas dos dados
        
        Returns:
            Dict: Estatísticas completas
        """
        # Análise de NCM por capítulo/posição
        ncm_analysis = defaultdict(lambda: defaultdict(int))
        
        for produto in self.medicamentos.values():
            ncm = produto.get('ncm', '')
            if ncm and len(ncm) >= 4:
                capitulo = ncm[:2]
                posicao = ncm[2:4]
                ncm_analysis[capitulo][posicao] += 1
        
        # Análise de CEST por segmento
        cest_analysis = defaultdict(lambda: defaultdict(int))
        
        for produto in self.medicamentos.values():
            cest = produto.get('cest', '')
            if cest and len(cest) >= 2:
                segmento = cest[:2]
                item = cest[2:5] if len(cest) >= 5 else ''
                cest_analysis[segmento][item] += 1
        
        return {
            'totais': {
                'registros_originais': self.stats['total_registros'],
                'produtos_unicos': self.stats['produtos_unicos'],
                'grupos_agregados': self.stats['grupos_agregados'],
                'ncms_unicos': len(self.stats['ncms_unicos']),
                'cests_unicos': len(self.stats['cests_unicos']),
                'laboratorios_unicos': len(self.stats['laboratorios_unicos'])
            },
            'ncms_detalhados': list(self.stats['ncms_unicos']),
            'cests_detalhados': list(self.stats['cests_unicos']),
            'analise_ncm_capitulo': dict(ncm_analysis),
            'analise_cest_segmento': dict(cest_analysis),
            'distribuicao_agregados': {
                'grupos_1_produto': sum(1 for grupo in self.agregados.values() if len(grupo) == 1),
                'grupos_multiplos': sum(1 for grupo in self.agregados.values() if len(grupo) > 1),
                'maior_grupo': max(len(grupo) for grupo in self.agregados.values()) if self.agregados else 0
            }
        }
    
    def exportar_dados(self, output_dir: str = "data/processed") -> Dict[str, str]:
        """
        Exporta dados processados para arquivos JSON
        
        Args:
            output_dir: Diretório de saída
            
        Returns:
            Dict: Caminhos dos arquivos gerados
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        arquivos_gerados = {}
        
        try:
            # 1. Medicamentos únicos
            medicamentos_file = output_path / "abc_farma_v2_medicamentos.json"
            with open(medicamentos_file, 'w', encoding='utf-8') as f:
                json.dump(self.medicamentos, f, ensure_ascii=False, indent=2)
            arquivos_gerados['medicamentos'] = str(medicamentos_file)
            
            # 2. Agregações
            agregados_file = output_path / "abc_farma_v2_agregados.json"
            with open(agregados_file, 'w', encoding='utf-8') as f:
                json.dump(self.agregados, f, ensure_ascii=False, indent=2)
            arquivos_gerados['agregados'] = str(agregados_file)
            
            # 3. Índices
            indices_file = output_path / "abc_farma_v2_indices.json"
            indices_data = {
                'ncm_index': dict(self.ncm_index),
                'cest_index': dict(self.cest_index),
                'codigo_barras_index': self.codigo_barras_index
            }
            with open(indices_file, 'w', encoding='utf-8') as f:
                json.dump(indices_data, f, ensure_ascii=False, indent=2)
            arquivos_gerados['indices'] = str(indices_file)
            
            # 4. Estatísticas
            stats_file = output_path / "abc_farma_v2_stats.json"
            stats_detalhadas = self.get_estatisticas_detalhadas()
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats_detalhadas, f, ensure_ascii=False, indent=2)
            arquivos_gerados['estatisticas'] = str(stats_file)
            
            # 5. Relatório de agregação
            agregacao_report = self.agregar_produtos_iguais()
            agregacao_file = output_path / "abc_farma_v2_agregacao_report.json"
            with open(agregacao_file, 'w', encoding='utf-8') as f:
                json.dump(agregacao_report, f, ensure_ascii=False, indent=2)
            arquivos_gerados['relatorio_agregacao'] = str(agregacao_file)
            
            # 6. Validação NCM/CEST
            validacao_report = self.validar_ncm_cest_consistency()
            validacao_file = output_path / "abc_farma_v2_validacao_ncm_cest.json"
            with open(validacao_file, 'w', encoding='utf-8') as f:
                json.dump(validacao_report, f, ensure_ascii=False, indent=2)
            arquivos_gerados['validacao_ncm_cest'] = str(validacao_file)
            
            logger.info(f"Dados exportados para {len(arquivos_gerados)} arquivos em {output_dir}")
            return arquivos_gerados
            
        except Exception as e:
            logger.error(f"Erro ao exportar dados: {e}")
            return {}

def main():
    """Função principal para teste do processador"""
    processor = ABCFarmaV2Processor()
    
    # Carregar amostra para teste (50k registros)
    if processor.carregar_dados(sample_size=50000):
        # Mostrar estatísticas
        stats = processor.get_estatisticas_detalhadas()
        print("📊 Estatísticas ABC Farma V2:")
        print(f"   Registros originais: {stats['totais']['registros_originais']:,}")
        print(f"   Produtos únicos: {stats['totais']['produtos_unicos']:,}")
        print(f"   Grupos agregados: {stats['totais']['grupos_agregados']:,}")
        print(f"   NCMs únicos: {stats['totais']['ncms_unicos']}")
        print(f"   CESTs únicos: {stats['totais']['cests_unicos']}")
        
        # Teste de busca
        print("\n🔍 Teste de busca por similaridade:")
        similares = processor.buscar_similares("DIPIRONA", limite=3)
        for med in similares:
            print(f"   {med['descricao']} - Score: {med['similarity_score']:.1f}%")
        
        # Exportar dados
        arquivos = processor.exportar_dados()
        print(f"\n💾 Arquivos gerados: {len(arquivos)}")
        for tipo, caminho in arquivos.items():
            print(f"   {tipo}: {caminho}")

if __name__ == "__main__":
    main()
