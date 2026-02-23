from typing import Any

from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    neighbourhood: str = Field(..., min_length=1)


class TierPrediction(BaseModel):
    predicted_tier: int = Field(..., ge=1, le=4)
    tier_label: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    model: str


class PredictResponse(TierPrediction):
    neighbourhood: str


class Neighbourhood(BaseModel):
    id: int
    name: str


class NeighbourhoodDetail(BaseModel):
    neighbourhood: str
    profile: dict[str, Any]
    cluster_id: int
    cluster_label: str
    prediction: TierPrediction


class ClusterDefinition(BaseModel):
    cluster_id: int
    cluster_label: str
    count: int
    neighbourhoods: list[str]


class AffordableNeighbourhood(BaseModel):
    neighbourhood: str
    avg_rent_1br: float
    cluster_id: int
    cluster_label: str
    predicted_tier: int
    tier_label: str
    confidence: float = Field(..., ge=0.0, le=1.0)


class AffordableResponse(BaseModel):
    annual_income: float
    monthly_budget: float
    neighbourhoods: list[AffordableNeighbourhood]


class MapNeighbourhood(BaseModel):
    neighbourhood: str
    geometry: dict[str, Any] | None
    avg_rent_1br: float
    cluster_id: int
    cluster_label: str
    predicted_tier: int = Field(..., ge=1, le=4)
    tier_label: str
    confidence: float = Field(..., ge=0.0, le=1.0)


class RentHistoryPoint(BaseModel):
    year: int
    avg_rent_1br: float


class NeighbourhoodHistoryResponse(BaseModel):
    neighbourhood: str
    history: list[RentHistoryPoint]
