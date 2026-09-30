import requests
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class SankhyaAPI:
    """Classe base responsável apenas por Autenticação e requisições HTTP para o Sankhya."""
    def __init__(self, client_id: str, client_secret: str, x_token: str, base_url: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.x_token = x_token
        self.base_api_url = base_url.rstrip('/')
        self.bearer_token = None

    def login(self) -> str:
        url = f"{self.base_api_url}/authenticate"
        headers = {'X-Token': self.x_token, 'Content-Type': 'application/x-www-form-urlencoded'}
        payload = {'client_id': self.client_id, 'client_secret': self.client_secret, 'grant_type': 'client_credentials'}
        
        try:
            response = requests.post(url, headers=headers, data=payload)
            response.raise_for_status()
            data = response.json()
            if "access_token" in data:
                self.bearer_token = data["access_token"]
                return self.bearer_token
            raise Exception(f"Failed to retrieve access_token. Response: {data}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Login failed: {e}")
            raise

    def execute_query(self, sql: str) -> List[Dict[str, Any]]:
        if not self.bearer_token:
            self.login()

        url = f"{self.base_api_url}/gateway/v1/mge/service.sbr?serviceName=DbExplorerSP.executeQuery&outputType=json"
        
        json_body = {
            "serviceName": "DbExplorerSP.executeQuery",
            "requestBody": {
                "sql": sql
            }
        }
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.bearer_token}'
        }
        
        try:
            response = requests.post(url, headers=headers, json=json_body)
            response.raise_for_status()
            
            response_data = response.json()
            if response_data.get('status') != '1':
                error_msg = response_data.get('statusMessage', 'Unknown Error')
                raise Exception(f"Sankhya API Error: {error_msg}")
                
            response_body = response_data.get('responseBody', {})
            records = []
            if 'fieldsMetadata' in response_body and 'rows' in response_body:
                fields = [f['name'] for f in response_body['fieldsMetadata']]
                for row in response_body['rows']:
                    record_dict = {}
                    for i, val in enumerate(row):
                        if i < len(fields):
                            record_dict[fields[i]] = val
                    records.append(record_dict)
            
            return records
        except requests.exceptions.RequestException as e:
            logger.error(f"Query execution failed: {e}")
            raise
