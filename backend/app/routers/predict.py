from fastapi import APIRouter, HTTPException
from ..schemas.models import PredictRequest, PredictResponse
from ..services import model as model_service

router = APIRouter()


@router.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    try:
        prediction = model_service.predict_neighbourhood(req.neighbourhood)
    except model_service.NeighbourhoodNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return PredictResponse(**prediction)
