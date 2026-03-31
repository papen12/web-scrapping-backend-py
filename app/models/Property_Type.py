from pydantic import BaseModel
class TipoPropiedadResponse(BaseModel):
    id_tipo_propiedad: int
    nombre_tipo_propiedad: str