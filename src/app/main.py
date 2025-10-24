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

@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "message": "Alert Manager API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint para monitoreo
    
    Verifica:
    - Estado de la API
    - Conexión a la base de datos
    - Timestamp del check
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    }
    
    # Verificar conexión a base de datos
    try:
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        health_status["database"] = "connected"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["database"] = f"error: {str(e)}"
        raise HTTPException(status_code=503, detail="Database connection failed")
    
    return health_status


@app.on_event("startup")
async def startup_event():
    """Evento al iniciar la aplicación"""
    print("🚀 Alert Manager API is starting up...")
    print(f"📚 Docs available at: /docs")
    print(f"🔍 Health check at: /health")


@app.on_event("shutdown")
async def shutdown_event():
    """Evento al cerrar la aplicación"""
    print("🛑 Alert Manager API is shutting down...")
