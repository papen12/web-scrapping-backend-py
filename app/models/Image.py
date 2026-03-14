from pydantic import BaseModel, Field, HttpUrl
from typing import Optional
from datetime import datetime

class ImagenBase(BaseModel):
    id_imagen: Optional[int] = None
    id_propiedad_fk: int
    nombre_imagen: str = Field(..., max_length=255)
    es_principal: bool = False
    storage_path: str
    public_url: Optional[HttpUrl] = None
    created_at: Optional[datetime] = None