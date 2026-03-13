from sqlalchemy import Column, Integer, String, Numeric, Text
from app.db.supabase import Base
from geoalchemy2 import Geometry

class Propiedad(Base):
    __tablename__ = "propiedad"

    id_propiedad = Column(Integer, primary_key=True, index=True)

    nombre_propiedad = Column(String(255))
    descripcion = Column(Text)
    direccion = Column(String)
    ubicacion_geografica = Column(Geometry("POINT", srid=4326))

    construccion_m2 = Column(Numeric(10,2))
    terreno_m2 = Column(Numeric(10,2))

    url_imagen = Column(String)

    precio_original = Column(Numeric(12,2))
    tipo_moneda = Column(String(3))

    precio_bob = Column(Numeric(12,2))
    precio_usd = Column(Numeric(12,2))

    cambio_utilizado = Column(Numeric(10,4))
    precio_m2_bob = Column(Numeric(10,2))
    precio_m2_usd = Column(Numeric(10,2))

    id_zona = Column(Integer)
    id_tipo_propiedad = Column(Integer)
    
    

