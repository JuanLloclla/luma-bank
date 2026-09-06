from pydantic import BaseModel
from typing import Optional

class DniOcrResponse(BaseModel):
    numero_dni: str
    nombres: str
    apellidos: str
    fecha_nacimiento: str
    fecha_vencimiento: str
    departamento: Optional[str] = None
    
    class Config:
        populate_by_name = True
