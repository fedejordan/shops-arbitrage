from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
from routers import products
from db_utils import init_db, check_database_connection
from error_handlers import add_exception_handlers

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Crear aplicación FastAPI
app = FastAPI(
    title="API de Arbitraje de Productos",
    description="API para buscar y comparar productos de diferentes tiendas",
    version="0.1.0",
)

# Agregar manejadores de excepciones
add_exception_handlers(app)

# Configurar CORS
origins = [
    "http://localhost:3000",
    "http://localhost:8000",
    # Agregar otros orígenes si es necesario
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Verificar conexión a la base de datos al inicio
@app.on_event("startup")
async def startup_db_client():
    if not init_db():
        logger.error("No se pudo inicializar la base de datos. La aplicación puede no funcionar correctamente.")

# Incluir routers
app.include_router(products.router)

@app.get("/")
def read_root():
    return {"message": "Bienvenido a la API de Arbitraje de Productos"}

@app.get("/health")
def health_check():
    """
    Endpoint para verificar el estado de la API y la conexión a la base de datos
    """
    db_status = check_database_connection()
    
    if not db_status:
        raise HTTPException(
            status_code=503, 
            detail="Error de conexión a la base de datos"
        )
    
    return {
        "status": "ok",
        "database_connection": "ok"
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)