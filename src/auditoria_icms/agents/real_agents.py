"""
Agentes Reais - Fase 6
Implementa agentes reais conectados aos dados estruturados NCM/CEST
"""

import json
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import logging
import re
from pathlib import Path

from ..core.config import get_settings


class NCMAgent:
    """Agente real para classificação NCM baseado em dados estruturados"""
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)
        self.ncm_data = None
        self.ncm_descriptions = None
        self._load_ncm_data()
    
    def _load_ncm_data(self):
        """Carrega dados NCM estruturados"""
        try:
            # Carregar Tabela NCM
            data_path = Path("data/raw")
            
            # Carregar Excel NCM
            if (data_path / "Tabela_NCM.xlsx").exists():
                ncm_df = pd.read_excel(data_path / "Tabela_NCM.xlsx")
                self.ncm_data = ncm_df.to_dict('records')
                self.logger.info(f"Carregados {len(self.ncm_data)} códigos NCM")
            
            # Carregar descrições hierárquicas
            if (data_path / "descricoes_ncm.json").exists():
                with open(data_path / "descricoes_ncm.json", 'r', encoding='utf-8') as f:
                    self.ncm_descriptions = json.load(f)
                self.logger.info("Descrições NCM hierárquicas carregadas")
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar dados NCM: {e}")
            self.ncm_data = []
            self.ncm_descriptions = {}
    
    def validate_ncm(self, ncm_code: str, description: str, empresa_atividade: str = None) -> Dict[str, Any]:
        """Valida código NCM existente"""
        try:
            if not ncm_code or len(ncm_code) != 8:
                return {
                    "valid": False,
                    "confidence": 0.0,
                    "reason": "Código NCM inválido ou formato incorreto",
                    "ncm_validado": None
                }
            
            # Buscar NCM na base
            ncm_info = self._find_ncm_by_code(ncm_code)
            
            if not ncm_info:
                return {
                    "valid": False,
                    "confidence": 0.0,
                    "reason": f"NCM {ncm_code} não encontrado na base",
                    "ncm_validado": None
                }
            
            # Calcular compatibilidade com descrição
            compatibility_score = self._calculate_description_compatibility(
                description, ncm_info.get('Descrição', ''), empresa_atividade
            )
            
            # Verificar hierarquia NCM
            hierarchy_info = self._analyze_ncm_hierarchy(ncm_code)
            
            return {
                "valid": compatibility_score > 0.6,
                "confidence": compatibility_score,
                "ncm_validado": ncm_code,
                "ncm_info": ncm_info,
                "hierarchy": hierarchy_info,
                "justificativa": f"NCM validado com confiança {compatibility_score:.2%}. {hierarchy_info['explanation']}"
            }
            
        except Exception as e:
            self.logger.error(f"Erro na validação NCM: {e}")
            return {
                "valid": False,
                "confidence": 0.0,
                "reason": f"Erro na validação: {str(e)}",
                "ncm_validado": None
            }
    
    def determine_ncm(self, description: str, empresa_atividade: str = None) -> Dict[str, Any]:
        """Determina código NCM para produto sem classificação"""
        try:
            # Buscar NCM por similaridade de descrição
            candidates = self._find_ncm_candidates(description, empresa_atividade)
            
            if not candidates:
                return {
                    "success": False,
                    "confidence": 0.0,
                    "reason": "Nenhum NCM candidato encontrado",
                    "ncm_determinado": None
                }
            
            # Selecionar melhor candidato
            best_candidate = max(candidates, key=lambda x: x['score'])
            
            if best_candidate['score'] < 0.5:
                return {
                    "success": False,
                    "confidence": best_candidate['score'],
                    "reason": "Confiança insuficiente na determinação",
                    "ncm_determinado": None,
                    "candidates": candidates[:3]  # Top 3
                }
            
            return {
                "success": True,
                "confidence": best_candidate['score'],
                "ncm_determinado": best_candidate['ncm'],
                "ncm_info": best_candidate['info'],
                "justificativa": f"NCM {best_candidate['ncm']} determinado com {best_candidate['score']:.2%} de confiança",
                "candidates": candidates[:3]
            }
            
        except Exception as e:
            self.logger.error(f"Erro na determinação NCM: {e}")
            return {
                "success": False,
                "confidence": 0.0,
                "reason": f"Erro na determinação: {str(e)}",
                "ncm_determinado": None
            }
    
    def _find_ncm_by_code(self, ncm_code: str) -> Optional[Dict]:
        """Busca NCM por código"""
        if not self.ncm_data:
            return None
        
        for item in self.ncm_data:
            if str(item.get('Código', '')).replace('.', '') == ncm_code.replace('.', ''):
                return item
        return None
    
    def _find_ncm_candidates(self, description: str, empresa_atividade: str = None) -> List[Dict]:
        """Busca candidatos NCM por descrição"""
        if not self.ncm_data:
            return []
        
        candidates = []
        description_lower = description.lower()
        
        # Palavras-chave da descrição
        keywords = self._extract_keywords(description_lower)
        
        for item in self.ncm_data:
            ncm_desc = str(item.get('Descrição', '')).lower()
            
            # Calcular score baseado em palavras-chave
            score = self._calculate_keyword_score(keywords, ncm_desc)
            
            # Boost baseado na atividade da empresa
            if empresa_atividade:
                score *= self._get_activity_boost(ncm_desc, empresa_atividade)
            
            if score > 0.3:  # Threshold mínimo
                candidates.append({
                    'ncm': item.get('Código'),
                    'score': score,
                    'info': item
                })
        
        return sorted(candidates, key=lambda x: x['score'], reverse=True)[:10]
    
    def _calculate_description_compatibility(self, product_desc: str, ncm_desc: str, empresa_atividade: str = None) -> float:
        """Calcula compatibilidade entre descrições"""
        if not product_desc or not ncm_desc:
            return 0.0
        
        product_lower = product_desc.lower()
        ncm_lower = ncm_desc.lower()
        
        # Palavras-chave em comum
        product_words = set(self._extract_keywords(product_lower))
        ncm_words = set(self._extract_keywords(ncm_lower))
        
        if not product_words or not ncm_words:
            return 0.0
        
        # Jaccard similarity
        intersection = len(product_words.intersection(ncm_words))
        union = len(product_words.union(ncm_words))
        
        base_score = intersection / union if union > 0 else 0
        
        # Boost por atividade
        if empresa_atividade:
            activity_boost = self._get_activity_boost(ncm_lower, empresa_atividade)
            base_score *= activity_boost
        
        return min(base_score, 1.0)
    
    def _analyze_ncm_hierarchy(self, ncm_code: str) -> Dict[str, Any]:
        """Analisa hierarquia do código NCM"""
        try:
            # Formato: AABB.CC.DD
            clean_code = ncm_code.replace('.', '')
            
            if len(clean_code) != 8:
                return {"error": "Formato NCM inválido"}
            
            capitulo = clean_code[:2]
            posicao = clean_code[:4]
            subposicao = clean_code[:6]
            item_subitem = clean_code[6:]
            
            return {
                "capitulo": capitulo,
                "posicao": posicao,
                "subposicao": subposicao,
                "item_subitem": item_subitem,
                "formatted": f"{posicao[:2]}{posicao[2:]}.{subposicao[4:]}.{item_subitem}",
                "explanation": f"Cap.{capitulo} > Pos.{posicao} > Sub.{subposicao} > Item.{item_subitem}"
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extrai palavras-chave relevantes"""
        # Remover palavras comuns
        stop_words = {'de', 'da', 'do', 'das', 'dos', 'para', 'com', 'em', 'na', 'no', 'e', 'ou', 'a', 'o', 'as', 'os'}
        
        # Dividir em palavras e filtrar
        words = re.findall(r'\b\w+\b', text.lower())
        keywords = [w for w in words if len(w) > 2 and w not in stop_words]
        
        return keywords
    
    def _calculate_keyword_score(self, keywords: List[str], target_text: str) -> float:
        """Calcula score baseado em palavras-chave"""
        if not keywords:
            return 0.0
        
        matches = sum(1 for keyword in keywords if keyword in target_text)
        return matches / len(keywords)
    
    def _get_activity_boost(self, ncm_desc: str, empresa_atividade: str) -> float:
        """Retorna boost baseado na atividade da empresa"""
        if not empresa_atividade:
            return 1.0
        
        atividade_lower = empresa_atividade.lower()
        
        # Mapeamentos de atividade para termos NCM
        activity_mapping = {
            'farmacia': ['medicamento', 'farmaceutico', 'droga', 'medicina'],
            'autopeças': ['veiculo', 'automovel', 'motor', 'peca'],
            'alimenticio': ['alimento', 'bebida', 'comestivel', 'nutricional'],
            'vestuario': ['roupa', 'tecido', 'vestimenta', 'confeccao'],
            'eletronico': ['eletronico', 'computador', 'telefone', 'digital']
        }
        
        for activity, terms in activity_mapping.items():
            if activity in atividade_lower:
                for term in terms:
                    if term in ncm_desc:
                        return 1.5  # 50% boost
        
        return 1.0


class CESTAgent:
    """Agente real para classificação CEST baseado em dados estruturados"""
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)
        self.cest_data = None
        self.cest_ro_data = None
        self._load_cest_data()
    
    def _load_cest_data(self):
        """Carrega dados CEST estruturados"""
        try:
            data_path = Path("data/raw")
            
            # Carregar Convênio 142
            if (data_path / "conv_142_formatado.json").exists():
                with open(data_path / "conv_142_formatado.json", 'r', encoding='utf-8') as f:
                    self.cest_data = json.load(f)
                self.logger.info(f"Carregados {len(self.cest_data)} itens CEST do Convênio 142")
            
            # Carregar CEST RO
            if (data_path / "CEST_RO.xlsx").exists():
                cest_ro_df = pd.read_excel(data_path / "CEST_RO.xlsx")
                self.cest_ro_data = cest_ro_df.to_dict('records')
                self.logger.info(f"Carregados {len(self.cest_ro_data)} itens CEST RO")
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar dados CEST: {e}")
            self.cest_data = []
            self.cest_ro_data = []
    
    def validate_cest(self, cest_code: str, ncm_code: str, description: str, empresa_atividade: str = None) -> Dict[str, Any]:
        """Valida código CEST existente"""
        try:
            if not cest_code:
                return {
                    "valid": True,
                    "confidence": 1.0,
                    "reason": "Produto sem CEST (válido para produtos que não se enquadram)",
                    "cest_validado": None
                }
            
            # Buscar CEST na base
            cest_info = self._find_cest_by_code(cest_code)
            
            if not cest_info:
                return {
                    "valid": False,
                    "confidence": 0.0,
                    "reason": f"CEST {cest_code} não encontrado na base",
                    "cest_validado": None
                }
            
            # Verificar compatibilidade com NCM
            ncm_compatibility = self._check_ncm_cest_compatibility(ncm_code, cest_code, cest_info)
            
            # Verificar segmento da empresa
            segment_compatibility = self._check_segment_compatibility(empresa_atividade, cest_info)
            
            # Score final
            final_score = min(ncm_compatibility['score'] * segment_compatibility['score'], 1.0)
            
            return {
                "valid": final_score > 0.7,
                "confidence": final_score,
                "cest_validado": cest_code if final_score > 0.7 else None,
                "cest_info": cest_info,
                "ncm_compatibility": ncm_compatibility,
                "segment_compatibility": segment_compatibility,
                "justificativa": f"CEST validado com {final_score:.2%} de confiança"
            }
            
        except Exception as e:
            self.logger.error(f"Erro na validação CEST: {e}")
            return {
                "valid": False,
                "confidence": 0.0,
                "reason": f"Erro na validação: {str(e)}",
                "cest_validado": None
            }
    
    def determine_cest(self, ncm_code: str, description: str, empresa_atividade: str = None) -> Dict[str, Any]:
        """Determina código CEST baseado no NCM e atividade"""
        try:
            # Buscar CEST candidatos baseado no NCM
            candidates = self._find_cest_candidates_by_ncm(ncm_code, description, empresa_atividade)
            
            if not candidates:
                return {
                    "success": True,  # É válido não ter CEST
                    "confidence": 1.0,
                    "reason": "Produto não se enquadra em nenhum CEST (válido)",
                    "cest_determinado": None
                }
            
            # Selecionar melhor candidato
            best_candidate = max(candidates, key=lambda x: x['score'])
            
            if best_candidate['score'] < 0.6:
                return {
                    "success": True,
                    "confidence": 0.8,
                    "reason": "Produto provavelmente não possui CEST",
                    "cest_determinado": None,
                    "candidates": candidates[:3]
                }
            
            return {
                "success": True,
                "confidence": best_candidate['score'],
                "cest_determinado": best_candidate['cest'],
                "cest_info": best_candidate['info'],
                "justificativa": f"CEST {best_candidate['cest']} determinado com {best_candidate['score']:.2%} de confiança",
                "candidates": candidates[:3]
            }
            
        except Exception as e:
            self.logger.error(f"Erro na determinação CEST: {e}")
            return {
                "success": False,
                "confidence": 0.0,
                "reason": f"Erro na determinação: {str(e)}",
                "cest_determinado": None
            }
    
    def _find_cest_by_code(self, cest_code: str) -> Optional[Dict]:
        """Busca CEST por código"""
        if self.cest_data:
            for item in self.cest_data:
                if item.get('cest') == cest_code:
                    return item
        
        if self.cest_ro_data:
            for item in self.cest_ro_data:
                if str(item.get('CEST', '')).replace('.', '') == cest_code.replace('.', ''):
                    return item
        
        return None
    
    def _find_cest_candidates_by_ncm(self, ncm_code: str, description: str, empresa_atividade: str = None) -> List[Dict]:
        """Busca candidatos CEST baseado no NCM"""
        candidates = []
        
        if self.cest_data:
            for item in self.cest_data:
                # Verificar se NCM está na lista do CEST
                ncm_match_score = self._calculate_ncm_match_score(ncm_code, item.get('ncm', ''))
                
                if ncm_match_score > 0:
                    # Score baseado na descrição
                    desc_score = self._calculate_description_score(description, item.get('descricao_oficial_cest', ''))
                    
                    # Score baseado no segmento da empresa
                    segment_score = self._calculate_segment_score(empresa_atividade, item.get('Segmento', ''))
                    
                    # Score final
                    final_score = ncm_match_score * 0.5 + desc_score * 0.3 + segment_score * 0.2
                    
                    if final_score > 0.3:
                        candidates.append({
                            'cest': item.get('cest'),
                            'score': final_score,
                            'info': item
                        })
        
        return sorted(candidates, key=lambda x: x['score'], reverse=True)[:5]
    
    def _calculate_ncm_match_score(self, ncm_code: str, cest_ncm_list: str) -> float:
        """Calcula score de compatibilidade NCM-CEST"""
        if not cest_ncm_list:
            return 0.0
        
        # Limpar códigos
        clean_ncm = ncm_code.replace('.', '')
        
        # Verificar matches exatos e parciais
        if clean_ncm in cest_ncm_list:
            return 1.0
        
        # Verificar por categorias (primeiros dígitos)
        for length in [6, 4, 2]:  # subposição, posição, capítulo
            if clean_ncm[:length] in cest_ncm_list:
                return 0.8 - (8 - length) * 0.1
        
        return 0.0
    
    def _check_ncm_cest_compatibility(self, ncm_code: str, cest_code: str, cest_info: Dict) -> Dict[str, Any]:
        """Verifica compatibilidade NCM-CEST"""
        ncm_list = cest_info.get('ncm', '')
        score = self._calculate_ncm_match_score(ncm_code, ncm_list)
        
        return {
            "score": score,
            "compatible": score > 0.5,
            "explanation": f"NCM {ncm_code} {'compatível' if score > 0.5 else 'incompatível'} com CEST {cest_code}"
        }
    
    def _check_segment_compatibility(self, empresa_atividade: str, cest_info: Dict) -> Dict[str, Any]:
        """Verifica compatibilidade de segmento"""
        if not empresa_atividade:
            return {"score": 1.0, "compatible": True, "explanation": "Atividade não informada"}
        
        segmento = cest_info.get('Segmento', '')
        
        # Verificações específicas para segmentos conhecidos
        atividade_lower = empresa_atividade.lower()
        
        segment_mapping = {
            'farmacia': ['13'],  # Medicamentos
            'autopecas': ['01'],  # Autopeças
            'alimenticio': ['03'],  # Alimentos
            'porta a porta': ['28']  # Venda porta a porta
        }
        
        for activity, segments in segment_mapping.items():
            if activity in atividade_lower:
                if any(seg in str(segmento) for seg in segments):
                    return {"score": 1.0, "compatible": True, "explanation": f"Segmento {segmento} compatível com {activity}"}
                else:
                    return {"score": 0.3, "compatible": False, "explanation": f"Segmento {segmento} pode não ser compatível com {activity}"}
        
        return {"score": 0.8, "compatible": True, "explanation": "Compatibilidade de segmento não verificada"}
    
    def _calculate_description_score(self, product_desc: str, cest_desc: str) -> float:
        """Calcula score baseado na descrição"""
        if not product_desc or not cest_desc:
            return 0.0
        
        product_lower = product_desc.lower()
        cest_lower = cest_desc.lower()
        
        # Palavras-chave em comum
        product_words = set(re.findall(r'\b\w+\b', product_lower))
        cest_words = set(re.findall(r'\b\w+\b', cest_lower))
        
        if not product_words or not cest_words:
            return 0.0
        
        intersection = len(product_words.intersection(cest_words))
        union = len(product_words.union(cest_words))
        
        return intersection / union if union > 0 else 0.0
    
    def _calculate_segment_score(self, empresa_atividade: str, segmento: str) -> float:
        """Calcula score baseado no segmento"""
        if not empresa_atividade or not segmento:
            return 0.5
        
        return self._check_segment_compatibility(empresa_atividade, {'Segmento': segmento})['score']
