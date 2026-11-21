
from pydantic import BaseModel, Field


class PrediccionEntrada(BaseModel):
    borough: str
    mes: int = Field(ge=1, le=12)
    semana_anio: int = Field(ge=1, le=53)

    lag_1: float = Field(ge=0)
    lag_2: float = Field(ge=0)
    lag_4: float = Field(ge=0)
    lag_52: float = Field(ge=0)

    media_movil_4: float = Field(gt=0)
    media_movil_12: float = Field(gt=0)
    media_movil_52: float = Field(gt=0)
    std_movil_4: float = Field(ge=0)


class PrediccionSalida(BaseModel):
    borough: str
    nivel_demanda: str
