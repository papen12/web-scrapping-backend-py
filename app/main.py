from fastapi import FastAPI
from app.routers import C21_Router,Remax_Rounter

app = FastAPI()
app.include_router(C21_Router.c21_router)
app.include_router(Remax_Rounter.remax_router)