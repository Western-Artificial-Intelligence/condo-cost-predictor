"""
Data validation schemas for condo-cost-predictor pipeline.

Each schema defines expected structure, types, and constraints
for a specific data table in the pipeline.
"""

from .neighbourhoods import NeighbourhoodsSchema
from .socioeconomics import SocioeconomicsSchema
from .housing_indicators import HousingIndicatorsSchema
from .permits import PermitsSchema
from .transit import TransitSchema
from .crime import CrimeSchema
from .parks import ParksSchema
from .macro import MacroSchema

__all__ = [
    "NeighbourhoodsSchema",
    "SocioeconomicsSchema",
    "HousingIndicatorsSchema",
    "PermitsSchema",
    "TransitSchema",
    "CrimeSchema",
    "ParksSchema",
    "MacroSchema",
]
