from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List
from dependencies import get_sankhya_api
from services.sankhya_api import SankhyaAPI
import requests
from datetime import datetime

router = APIRouter(prefix="/usuarios", tags=["Usuários"])

@router.get("/")
def get_usuarios(api: SankhyaAPI = Depends(get_sankhya_api)):
    if not api.bearer_token:
        api.login()
        
    url = f"{api.base_api_url}/gateway/v1/mge/service.sbr?serviceName=CRUDServiceProvider.loadRecords&outputType=json"
    
    req_body = {
        'serviceName': 'CRUDServiceProvider.loadRecords',
        'requestBody': {
            'dataSet': {
                'rootEntity': 'Usuario',
                'includePresentationFields': 'S',
                'offsetPage': '0',
                'dataRow': {'keys': {}, 'localFields': {}},
                'entity': {
                    'fieldset': {'list': 'CODUSU,NOMEUSU,DTULTACESSO'},
                    'criteria': {'expression': '1=1'}
                }
            }
        }
    }
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api.bearer_token}'
    }
    
    try:
        response = requests.post(url, headers=headers, json=req_body)
        response.raise_for_status()
        
        data = response.json()
        if data.get('status') != '1':
            raise Exception(f"Sankhya Error: {data.get('statusMessage')}")
            
        entities = data.get('responseBody', {}).get('entities', {}).get('entity', [])
        
        # Transform array [{f0: {'$': '1'}, f1: ...}] to clean dict
        usuarios = []
        for e in entities:
            cod = e.get('f0', {}).get('$')
            nome = e.get('f1', {}).get('$')
            dt_ultimo_acesso = e.get('f2', {}).get('$')
            
            # Parse datetime for sorting
            dt_obj = datetime.min
            if dt_ultimo_acesso:
                try:
                    dt_obj = datetime.strptime(dt_ultimo_acesso, "%d/%m/%Y %H:%M:%S")
                except ValueError:
                    pass
            
            usuarios.append({
                "CODUSU": cod,
                "NOMEUSU": nome,
                "DTULTACESSO": dt_ultimo_acesso,
                "_dt_obj": dt_obj
            })
            
        # Ordenar por data de ultimo acesso (mais recentes primeiro), ignorando vazios
        usuarios.sort(key=lambda x: x['_dt_obj'], reverse=True)
        
        # Remove the internal datetime object before returning
        for u in usuarios:
            del u['_dt_obj']
        
        return usuarios
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
