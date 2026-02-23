from fastapi import APIRouter, HTTPException, Query

from ..schemas.models import (
    AffordableResponse,
    ClusterDefinition,
    Neighbourhood,
    NeighbourhoodDetail,
)
from ..services import model as model_service

router = APIRouter()


@router.get("/neighbourhoods", response_model=list[Neighbourhood])
def list_neighbourhoods():
    return model_service.list_neighbourhoods()


@router.get("/neighbourhood/{name}", response_model=NeighbourhoodDetail)
def get_neighbourhood(name: str):
    try:
        return model_service.neighbourhood_detail(name)
    except model_service.NeighbourhoodNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/clusters", response_model=list[ClusterDefinition])
def get_clusters():
    return model_service.clusters()


@router.get("/affordable", response_model=AffordableResponse)
def get_affordable(income: float = Query(..., gt=0)):
    return model_service.affordable_neighbourhoods(income)
