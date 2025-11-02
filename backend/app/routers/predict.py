from fastapi import APIRouter
from ..schemas.models import PredictRequest, PredictResponse
from ..services import model as model_service

router = APIRouter()

@router.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    price, model_name = model_service.predict(req)
    return PredictResponse(predicted_price=price, model=model_name)
