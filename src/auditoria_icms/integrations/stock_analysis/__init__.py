"""
__init__.py para integração com sistemas de análise de estoques
"""

from .stock_adapter import (
    StockItem,
    ClassificationResult,
    StockAnalysisAdapter,
    GenericStockAdapter,
    StockIntegrationManager,
)

__all__ = [
    "StockItem",
    "ClassificationResult",
    "StockAnalysisAdapter",
    "GenericStockAdapter",
    "StockIntegrationManager",
]
