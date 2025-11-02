from ..schemas.models import PredictRequest

def predict(req: PredictRequest) -> tuple[float, str]:
    # deterministic placeholder model for sprint 1 rn 
    base = 200_000
    price = base + req.sqft * 900 + req.bedrooms * 75_000 + int(req.bathrooms) * 50_000
    return float(price), "mock-linear"
