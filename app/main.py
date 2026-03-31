from fastapi import FastAPI
from app.routers import C21_Router, Kriging_Router,Remax_Router,Property_Router,Interest_Point_Router,Property_Type_Router
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

origins = [
    "http://localhost:4321",
    "http://127.0.0.1:4321"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  
    allow_credentials=True,
    allow_methods=["*"],   
    allow_headers=["*"],   
)

app.include_router(C21_Router.c21_router)
app.include_router(Remax_Router.remax_router)
app.include_router(Property_Router.property_router)
app.include_router(Interest_Point_Router.interest_point_router)
app.include_router(Kriging_Router.kriging_router)
app.include_router(Property_Type_Router.type_property_router)