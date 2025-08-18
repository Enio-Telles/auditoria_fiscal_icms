"""
Interface de Integração com Sistemas de Análise de Estoques
Módulo preparado para integração futura com sistemas externos de análise de estoques.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import json
import logging


@dataclass
class StockItem:
    """Representa um item de estoque para análise fiscal."""
    item_id: str
    description: str
    gtin: Optional[str] = None
    ncm_current: Optional[str] = None
    cest_current: Optional[str] = None
    supplier: Optional[str] = None
    category: Optional[str] = None
    unit_price: Optional[float] = None
    quantity: Optional[int] = None
    last_updated: Optional[datetime] = None


@dataclass
class ClassificationResult:
    """Resultado de classificação fiscal para item de estoque."""
    item_id: str
    ncm_suggested: str
    cest_suggested: str
    confidence_score: float
    justification: str
    requires_review: bool
    processed_at: datetime


class StockAnalysisAdapter(ABC):
    """
    Interface base para adaptadores de sistemas de análise de estoques.
    Define o contrato para integração com diferentes ERPs e sistemas de estoque.
    """
    
    @abstractmethod
    async def connect(self, connection_config: Dict[str, Any]) -> bool:
        """Estabelece conexão com o sistema de estoque."""
        pass
    
    @abstractmethod
    async def fetch_items(self, filters: Optional[Dict[str, Any]] = None) -> List[StockItem]:
        """Busca itens do estoque que precisam de análise fiscal."""
        pass
    
    @abstractmethod
    async def update_classification(self, item_id: str, classification: ClassificationResult) -> bool:
        """Atualiza a classificação fiscal de um item no sistema."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """Encerra conexão com o sistema."""
        pass


class GenericStockAdapter(StockAnalysisAdapter):
    """
    Adaptador genérico para sistemas de estoque via API REST ou arquivos.
    Implementação base que pode ser estendida para sistemas específicos.
    """
    
    def __init__(self, adapter_config: Dict[str, Any]):
        self.config = adapter_config
        self.logger = logging.getLogger(__name__)
        self.connection_active = False
        self.supported_formats = ['json', 'csv', 'xml']
        
    async def connect(self, connection_config: Dict[str, Any]) -> bool:
        """Conecta ao sistema de estoque."""
        try:
            connection_type = connection_config.get('type', 'file')
            
            if connection_type == 'api':
                return await self._connect_api(connection_config)
            elif connection_type == 'file':
                return await self._connect_file(connection_config)
            elif connection_type == 'database':
                return await self._connect_database(connection_config)
            else:
                self.logger.error(f"Tipo de conexão não suportado: {connection_type}")
                return False
                
        except Exception as e:
            self.logger.error(f"Erro na conexão: {str(e)}")
            return False
    
    async def _connect_api(self, config: Dict[str, Any]) -> bool:
        """Conecta via API REST."""
        api_url = config.get('api_url')
        api_key = config.get('api_key')
        
        if not api_url:
            self.logger.error("URL da API não fornecida")
            return False
        
        # Implementação futura: testar conexão com API
        self.logger.info(f"Conectando à API: {api_url}")
        self.connection_active = True
        return True
    
    async def _connect_file(self, config: Dict[str, Any]) -> bool:
        """Conecta via arquivos locais."""
        file_path = config.get('file_path')
        
        if not file_path:
            self.logger.error("Caminho do arquivo não fornecido")
            return False
        
        # Verificar se arquivo existe e é legível
        from pathlib import Path
        if not Path(file_path).exists():
            self.logger.error(f"Arquivo não encontrado: {file_path}")
            return False
        
        self.connection_active = True
        self.logger.info(f"Conectado ao arquivo: {file_path}")
        return True
    
    async def _connect_database(self, config: Dict[str, Any]) -> bool:
        """Conecta via banco de dados."""
        # Implementação futura para conexões diretas com BD
        self.logger.info("Conexão com banco de dados não implementada ainda")
        return False
    
    async def fetch_items(self, filters: Optional[Dict[str, Any]] = None) -> List[StockItem]:
        """Busca itens do estoque."""
        if not self.connection_active:
            self.logger.error("Conexão não estabelecida")
            return []
        
        try:
            connection_type = self.config.get('connection_type', 'file')
            
            if connection_type == 'api':
                return await self._fetch_from_api(filters)
            elif connection_type == 'file':
                return await self._fetch_from_file(filters)
            else:
                return []
                
        except Exception as e:
            self.logger.error(f"Erro ao buscar itens: {str(e)}")
            return []
    
    async def _fetch_from_api(self, filters: Optional[Dict[str, Any]]) -> List[StockItem]:
        """Busca itens via API."""
        # Implementação futura
        self.logger.info("Busca via API não implementada ainda")
        return []
    
    async def _fetch_from_file(self, filters: Optional[Dict[str, Any]]) -> List[StockItem]:
        """Busca itens de arquivo."""
        file_path = self.config.get('file_path')
        
        if not file_path:
            return []
        
        try:
            from pathlib import Path
            file_ext = Path(file_path).suffix.lower()
            
            if file_ext == '.json':
                return await self._parse_json_file(file_path, filters)
            elif file_ext == '.csv':
                return await self._parse_csv_file(file_path, filters)
            elif file_ext == '.xml':
                return await self._parse_xml_file(file_path, filters)
            else:
                self.logger.error(f"Formato de arquivo não suportado: {file_ext}")
                return []
                
        except Exception as e:
            self.logger.error(f"Erro ao processar arquivo: {str(e)}")
            return []
    
    async def _parse_json_file(self, file_path: str, filters: Optional[Dict[str, Any]]) -> List[StockItem]:
        """Parse de arquivo JSON."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            items = []
            
            # Assumir que dados estão em lista ou têm chave 'items'
            items_data = data if isinstance(data, list) else data.get('items', [])
            
            for item_data in items_data:
                if self._item_matches_filters(item_data, filters):
                    item = self._create_stock_item(item_data)
                    if item:
                        items.append(item)
            
            return items
            
        except Exception as e:
            self.logger.error(f"Erro ao processar JSON: {str(e)}")
            return []
    
    async def _parse_csv_file(self, file_path: str, filters: Optional[Dict[str, Any]]) -> List[StockItem]:
        """Parse de arquivo CSV."""
        try:
            import pandas as pd
            
            df = pd.read_csv(file_path)
            items = []
            
            for _, row in df.iterrows():
                item_data = row.to_dict()
                if self._item_matches_filters(item_data, filters):
                    item = self._create_stock_item(item_data)
                    if item:
                        items.append(item)
            
            return items
            
        except Exception as e:
            self.logger.error(f"Erro ao processar CSV: {str(e)}")
            return []
    
    async def _parse_xml_file(self, file_path: str, filters: Optional[Dict[str, Any]]) -> List[StockItem]:
        """Parse de arquivo XML."""
        try:
            import xml.etree.ElementTree as ET
            
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            items = []
            
            # Assumir estrutura genérica de XML
            for item_elem in root.findall('.//item') or root.findall('.//produto'):
                item_data = {}
                for child in item_elem:
                    item_data[child.tag] = child.text
                
                if self._item_matches_filters(item_data, filters):
                    item = self._create_stock_item(item_data)
                    if item:
                        items.append(item)
            
            return items
            
        except Exception as e:
            self.logger.error(f"Erro ao processar XML: {str(e)}")
            return []
    
    def _create_stock_item(self, item_data: Dict[str, Any]) -> Optional[StockItem]:
        """Cria objeto StockItem a partir de dados brutos."""
        try:
            # Mapeamento flexível de campos
            field_mappings = {
                'item_id': ['id', 'item_id', 'codigo', 'sku'],
                'description': ['description', 'descricao', 'nome', 'produto'],
                'gtin': ['gtin', 'ean', 'codigo_barras', 'barcode'],
                'ncm_current': ['ncm', 'ncm_atual', 'classificacao_ncm'],
                'cest_current': ['cest', 'cest_atual', 'classificacao_cest'],
                'supplier': ['fornecedor', 'supplier', 'fabricante'],
                'category': ['categoria', 'category', 'tipo'],
                'unit_price': ['preco', 'price', 'valor_unitario'],
                'quantity': ['quantidade', 'quantity', 'estoque']
            }
            
            # Extrair valores usando mapeamento
            extracted_data = {}
            
            for field, possible_keys in field_mappings.items():
                value = None
                for key in possible_keys:
                    if key in item_data and item_data[key] is not None:
                        value = item_data[key]
                        break
                extracted_data[field] = value
            
            # Validar campos obrigatórios
            if not extracted_data['item_id'] or not extracted_data['description']:
                return None
            
            # Converter tipos quando necessário
            if extracted_data['unit_price']:
                try:
                    extracted_data['unit_price'] = float(extracted_data['unit_price'])
                except (ValueError, TypeError):
                    extracted_data['unit_price'] = None
            
            if extracted_data['quantity']:
                try:
                    extracted_data['quantity'] = int(extracted_data['quantity'])
                except (ValueError, TypeError):
                    extracted_data['quantity'] = None
            
            return StockItem(
                item_id=str(extracted_data['item_id']),
                description=str(extracted_data['description']),
                gtin=str(extracted_data['gtin']) if extracted_data['gtin'] else None,
                ncm_current=str(extracted_data['ncm_current']) if extracted_data['ncm_current'] else None,
                cest_current=str(extracted_data['cest_current']) if extracted_data['cest_current'] else None,
                supplier=str(extracted_data['supplier']) if extracted_data['supplier'] else None,
                category=str(extracted_data['category']) if extracted_data['category'] else None,
                unit_price=extracted_data['unit_price'],
                quantity=extracted_data['quantity'],
                last_updated=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Erro ao criar StockItem: {str(e)}")
            return None
    
    def _item_matches_filters(self, item_data: Dict[str, Any], filters: Optional[Dict[str, Any]]) -> bool:
        """Verifica se item corresponde aos filtros especificados."""
        if not filters:
            return True
        
        try:
            # Filtros simples por igualdade
            for filter_key, filter_value in filters.items():
                if filter_key in item_data:
                    if item_data[filter_key] != filter_value:
                        return False
            
            return True
            
        except Exception:
            return True  # Em caso de erro, incluir item
    
    async def update_classification(self, item_id: str, classification: ClassificationResult) -> bool:
        """Atualiza classificação fiscal no sistema."""
        try:
            # Para implementação futura
            # Por enquanto, apenas log da atualização
            self.logger.info(
                f"Atualizando classificação para item {item_id}: "
                f"NCM={classification.ncm_suggested}, "
                f"CEST={classification.cest_suggested}, "
                f"Confiança={classification.confidence_score:.2%}"
            )
            
            # Aqui seria implementada a lógica específica para cada tipo de sistema
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao atualizar classificação: {str(e)}")
            return False
    
    async def disconnect(self) -> bool:
        """Encerra conexão."""
        self.connection_active = False
        self.logger.info("Conexão encerrada")
        return True


class StockIntegrationManager:
    """
    Gerenciador de integrações com sistemas de análise de estoques.
    Coordena múltiplos adaptadores e fornece interface unificada.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.adapters: Dict[str, StockAnalysisAdapter] = {}
        self.enabled = config.get('enabled', False)
        
    def register_adapter(self, name: str, adapter: StockAnalysisAdapter):
        """Registra um adaptador de sistema de estoque."""
        self.adapters[name] = adapter
        self.logger.info(f"Adaptador {name} registrado")
        
    async def analyze_stock_items(self, system_name: str) -> List[ClassificationResult]:
        """
        Analisa itens de estoque de um sistema específico.
        
        Args:
            system_name: Nome do sistema registrado
            
        Returns:
            Lista de resultados de classificação
        """
        if not self.enabled:
            self.logger.info("Integração com sistemas de estoque desabilitada")
            return []
        
        if system_name not in self.adapters:
            self.logger.error(f"Adaptador {system_name} não encontrado")
            return []
        
        adapter = self.adapters[system_name]
        
        try:
            # Buscar itens que precisam de análise
            items = await adapter.fetch_items({
                'needs_classification': True  # Filtro exemplo
            })
            
            self.logger.info(f"Encontrados {len(items)} itens para análise")
            
            # Aqui seria feita a integração com o sistema de classificação principal
            results = []
            
            for item in items:
                # Placeholder para classificação real
                result = ClassificationResult(
                    item_id=item.item_id,
                    ncm_suggested="00000000",  # Seria resultado real
                    cest_suggested="",
                    confidence_score=0.0,
                    justification="Análise pendente de implementação",
                    requires_review=True,
                    processed_at=datetime.now()
                )
                results.append(result)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Erro na análise de itens: {str(e)}")
            return []
    
    async def sync_classifications(self, system_name: str, results: List[ClassificationResult]) -> bool:
        """
        Sincroniza classificações de volta para o sistema de estoque.
        
        Args:
            system_name: Nome do sistema
            results: Resultados de classificação para sincronizar
            
        Returns:
            True se sucesso, False caso contrário
        """
        if not self.enabled or system_name not in self.adapters:
            return False
        
        adapter = self.adapters[system_name]
        success_count = 0
        
        for result in results:
            try:
                if await adapter.update_classification(result.item_id, result):
                    success_count += 1
            except Exception as e:
                self.logger.error(f"Erro ao sincronizar item {result.item_id}: {str(e)}")
        
        self.logger.info(f"Sincronizados {success_count}/{len(results)} itens")
        return success_count == len(results)
    
    def get_integration_status(self) -> Dict[str, Any]:
        """Retorna status das integrações."""
        return {
            "enabled": self.enabled,
            "registered_adapters": list(self.adapters.keys()),
            "total_adapters": len(self.adapters)
        }
