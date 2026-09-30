import os
from fastapi import HTTPException, Query
from services.sankhya_api import SankhyaAPI

def get_sankhya_api(env: str = Query("sandbox", description="Ambiente: sandbox ou producao")) -> SankhyaAPI:
    if env.lower() == "producao":
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
        raise HTTPException(status_code=500, detail=f"Missing Sankhya credentials for environment {env}")
        
    return SankhyaAPI(client_id, client_secret, x_token, base_url)
