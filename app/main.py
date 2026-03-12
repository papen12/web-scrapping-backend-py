from fastapi import FastAPI
from app.routers import C21_Router,Remax_Router,Property_Router

app = FastAPI()
app.include_router(C21_Router.c21_router)
app.include_router(Remax_Router.remax_router)
app.include_router(Property_Router.property_router)