"""
Endpoints da API FastAPI
Módulo de endpoints organizados por funcionalidade
"""

# Importar todos os routers dos endpoints
from . import auth
from . import users  
from . import companies
from . import data_import
from . import classification
from . import agents
from . import results
from . import golden_set

__all__ = [
    "auth",
    "users", 
    "companies",
    "data_import",
    "classification", 
    "agents",
    "results",
    "golden_set"
]
