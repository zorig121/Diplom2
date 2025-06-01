# app/main.py

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import auth, reset_password
from app.core.config import config
from app.db.mongodb import db_client
from backend.app.api.routes import containers

app = FastAPI()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    print("Connecting to MongoDB...")
    yield
    # Shutdown logic
    print("Closing MongoDB connection...")
    db_client.close()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[config.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router)
app.include_router(containers.router)
app.include_router(reset_password.router)

@app.get("/")
def root():
    return {"message": "Server is running"}
