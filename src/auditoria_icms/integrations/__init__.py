"""
__init__.py para módulo de integrações
"""

from .stock_analysis import (
    StockItem,
    ClassificationResult,
    StockAnalysisAdapter,
    GenericStockAdapter,
    StockIntegrationManager
)

__all__ = [
    'StockItem',
    'ClassificationResult', 
    'StockAnalysisAdapter',
    'GenericStockAdapter',
    'StockIntegrationManager'
]
