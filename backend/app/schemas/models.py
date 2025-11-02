from pydantic import BaseModel

class PredictRequest(BaseModel):
    bedrooms: int
    bathrooms: float
    sqft: int
    neighbourhood: str
    year: int

class PredictResponse(BaseModel):
    predicted_price: float
    currency: str = "CAD"
    model: str = "baseline"

class Neighbourhood(BaseModel):
    id: int
    name: str
