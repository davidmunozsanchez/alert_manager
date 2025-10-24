from fastapi import FastAPI
from app.routers import alerts
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Weather Alerts API",
    description="Gestión de alertas meteorológicas y otros tipos",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir todas las URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(alerts.router)

