from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from . import Base

class NeighbourhoodORM(Base):
    __tablename__ = "neighbourhoods"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
