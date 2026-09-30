from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from typing import Optional

from services.sankhya_service import SankhyaService
from dotenv import load_dotenv

load_dotenv(override=True)

app = FastAPI(title="Sankhya Comparador de Dados API", version="1.0.0")

# Routers
from routers import usuarios
app.include_router(usuarios.router, prefix="/api")

# Configure CORS
origins = os.environ.get("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir Frontend
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

def get_sankhya_service(env_choice: str = "sandbox"):
    if env_choice.lower() == "producao":
        client_id = os.environ.get("SANKHYA_PROD_CLIENT_ID")
        client_secret = os.environ.get("SANKHYA_PROD_CLIENT_SECRET")
        x_token = os.environ.get("SANKHYA_PROD_X_TOKEN")
        base_url = os.environ.get("SANKHYA_PROD_BASE_URL", "https://api.sankhya.com.br")
    else:
        client_id = os.environ.get("SANKHYA_CLIENT_ID")
        client_secret = os.environ.get("SANKHYA_CLIENT_SECRET")
        x_token = os.environ.get("SANKHYA_X_TOKEN")
        base_url = os.environ.get("SANKHYA_BASE_URL", "https://api.sandbox.sankhya.com.br")
        
    if not all([client_id, client_secret, x_token]):
        raise HTTPException(status_code=500, detail=f"Missing Sankhya credentials for environment {env_choice}")
        
    return SankhyaService(client_id, client_secret, x_token, base_url)

@app.get("/")
def read_root():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

@app.get("/api/status")
def get_api_status(env: str = Query("sandbox")):
    try:
        service = get_sankhya_service(env)
        service.login()
        return {"status": "online", "message": f"Conectado ao Sankhya API Gateway ({env})"}
    except Exception as e:
        return {"status": "offline", "message": str(e)}

@app.get("/api/vendas")
def get_vendas(
    start_date: str = Query(..., description="Data Inicial (DD/MM/YYYY)"),
    end_date: str = Query(..., description="Data Final (DD/MM/YYYY)"),
    vendedor: Optional[str] = None,
    env: str = Query("sandbox", description="Ambiente: sandbox ou producao")
):
    try:
        service = get_sankhya_service(env)
        return service.get_vendas(start_date, end_date, vendedor)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/compras")
def get_compras(
    start_date: str = Query(..., description="Data Inicial (DD/MM/YYYY)"),
    end_date: str = Query(..., description="Data Final (DD/MM/YYYY)"),
    fornecedor: Optional[str] = None,
    env: str = Query("sandbox", description="Ambiente: sandbox ou producao")
):
    try:
        service = get_sankhya_service(env)
        return service.get_compras(start_date, end_date, fornecedor)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/produtos")
def get_produtos(busca: Optional[str] = None, env: str = Query("sandbox")):
    try:
        service = get_sankhya_service(env)
        return service.get_produtos(busca)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/parceiros")
def get_parceiros(busca: Optional[str] = None, tipo: Optional[str] = None, env: str = Query("sandbox")):
    try:
        service = get_sankhya_service(env)
        return service.get_parceiros(busca, tipo)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/vendedores")
def get_vendedores(busca: Optional[str] = None, env: str = Query("sandbox")):
    try:
        service = get_sankhya_service(env)
        return service.get_vendedores(busca)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
