from fastapi import APIRouter
from sqlalchemy import select
from ..schemas.models import Neighbourhood
from ..services.db import get_session, is_db_enabled
from ..models.neighbourhood import NeighbourhoodORM

router = APIRouter()

# fallback mock in the event the db isn't enabled yet 
_MOCKS = [
    {"id": 1, "name": "Toronto C01"},
    {"id": 2, "name": "Toronto C08"},
    {"id": 3, "name": "Waterfront Communities-The Island"},
]

@router.get("/neighbourhoods", response_model=list[Neighbourhood])
def list_neighbourhoods():
    if not is_db_enabled():
        return _MOCKS
    with get_session() as db:
        rows = db.execute(select(NeighbourhoodORM.id, NeighbourhoodORM.name)).all()
        return [{"id": r.id, "name": r.name} for r in rows]
