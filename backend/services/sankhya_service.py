import requests
from typing import Optional, List, Dict, Any
import logging
import os

logger = logging.getLogger(__name__)

class SankhyaService:
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
            response = requests.post(url, json=json_body, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            status = data.get('status', '0')
            if status != '1':
                error_msg = data.get('statusMessage', 'Unknown error')
                raise Exception(f"Sankhya API Error: {error_msg}")
                
            records = []
            response_body = data.get('responseBody', {})
            
            if 'fieldsMetadata' in response_body and 'rows' in response_body:
                fields = [f.get('name') for f in response_body['fieldsMetadata']]
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

    # 1. VENDAS (Baseado no XML 1402)
    def get_vendas(self, start_date: str, end_date: str, cod_vendedor: Optional[str] = None) -> List[Dict[str, Any]]:
        safe_start = start_date.replace("'", "''")
        safe_end = end_date.replace("'", "''")
        
        # Filtro de vendedor opcional (na TGFCAB o campo é CODVEND)
        filtro_vendedor = ""
        if cod_vendedor:
            safe_vend = cod_vendedor.replace("'", "''")
            filtro_vendedor = f"AND CAB.CODVEND = {safe_vend}"

        # SQL Extraído do Dashboard 1402 (Apuração de ICMS por CFOP)
        # Fixado para Vendas (TIPMOV = 'V') e CFOP = 5102
        query = f"""
        SELECT * FROM (
        SELECT 
          UFSPAR.UF AS "UF"
        , PRO.CODPROD AS "Cód. Prod"
        , PRO.REFFORN AS "Cátalogo"
        , PRO.REFERENCIA AS "Ref Prod"
        , PAR.CODPARC AS "Cod. Parc"
        , PAR.RAZAOSOCIAL AS "Razão Social"
        , PAR.CGC_CPF AS "CNPJ_PARCEIRO"
        , PER.DESCRTIPPARC AS "Perfil"
        , CAB.NUMNOTA AS "Nro Nota"
        , CAB.DTFATUR AS "Dt. Emissão"
        , CAB.DTNEG AS "Dt. Ent Sai"
        , PRO.DESCRPROD AS "Descrição"
        , GRU.CODGRUPOPROD AS "GRUPO"
        , GRU.DESCRGRUPOPROD AS "GRUPODESCRICAO"
        , PRO.NCM AS "NCM"
        , ITE.CODCFO AS "CFOP"
        , PRO.MARCA AS "MARCA"
        , ITE.QTDNEG AS "Qtd Com"
        , ITE.VLRUNIT AS "Vlr. Unit"
        , ITE.VLRTOT AS "Vlr. Total"
        , ITE.BASEICMS AS "Base ICMS"
        , ITE.ALIQICMS AS "Aliq. ICMS"
        , ITE.VLRICMS AS "Vlr. ICMS"
        , (CASE WHEN ITE.VLRTOT = 0 OR CAB.VLRFRETE = 0 THEN 0 ELSE ITE.VLRTOT / (SELECT SUM( ITE.VLRTOT ) FROM TGFITE ITE WHERE ITE.NUNOTA = CAB.NUNOTA AND ITE.SEQUENCIA > 0) END)*CAB.VLRFRETE * (ITE.ALIQICMS/100) AS "Vlr. ICMS Frete"
        , ITE.VLRIPI AS "Vlr IPI"
        , ITE.VLRSUBST AS "Vlr ST"
        , ITE.BASESUBSTIT AS "Base ST"
        , ITE.CONTROLE AS "CONTROLE"
        , (CASE WHEN ITE.VLRTOT = 0 OR CAB.VLRFRETE = 0 THEN 0 ELSE ITE.VLRTOT / (SELECT SUM( ITE.VLRTOT ) FROM TGFITE ITE WHERE ITE.NUNOTA = CAB.NUNOTA AND ITE.SEQUENCIA > 0) END)*CAB.VLRFRETE AS "Vlr Frete"
        , TPO.CODTIPOPER AS "Cod TOP"
        , TPO.DESCROPER AS "TOP"
        , ITE.VLRDESC AS "Vlr Desc"
        , (SELECT O1.OPCAO FROM TDDOPC O1 WHERE O1.NUCAMPO = 765 AND O1.VALOR = CAB.CIF_FOB) AS "Tipo Frete"
        , (CASE WHEN ITE.VLRTOT = 0 OR CAB.VLROUTROS = 0 THEN 0 ELSE ITE.VLRTOT / (SELECT SUM( ITE.VLRTOT ) FROM TGFITE ITE WHERE ITE.NUNOTA = CAB.NUNOTA AND ITE.SEQUENCIA > 0 ) END)*CAB.VLROUTROS AS "Vlr Outros"
        , (SELECT O1.OPCAO FROM TDDOPC O1 WHERE O1.NUCAMPO = 856 AND O1.VALOR = CAB.TIPMOV) AS "TIPMOV"
        , ITE.VLRREPRED  AS "Vlr. Repasse Redução"
        , (SELECT SUM(D1.VLRDIFALDEST) FROM TGFDIN D1 WHERE D1.NUNOTA = CAB.NUNOTA AND D1.SEQUENCIA = ITE.SEQUENCIA) AS "Vlr. Difal Dest"
        , (SELECT SUM(D1.VLRDIFALREM)  FROM TGFDIN D1 WHERE D1.NUNOTA = CAB.NUNOTA AND D1.SEQUENCIA = ITE.SEQUENCIA) AS "Vlr. Difal Orig"
        , CAB.AD_PACIENTE AS "PACIENTE"
        , CAB.AD_CLIENTEUSO AS "COD_CLI_USO"
        , USO.RAZAOSOCIAL AS "RAZ_CLI_USO"
        , USO.CGC_CPF AS "CNPJ_PARC_USO"
        , CAB.AD_CONVENIO AS "CONVENIO"
        , CAB.AD_NUMEROCONTRATOCLIENTE AS "CONTRATO_CLIENTE"
        , CIDPAR.NOMECID AS "CIDADE"
        , (ITE.VLRTOT - ITE.VLRDESC) AS "Vlr. Contabil"
        , '' AS "PIS"
        , '' AS "COFINS"
        FROM TGFCAB CAB
        INNER JOIN TGFPAR PAR ON CAB.CODPARC = PAR.CODPARC
        INNER JOIN TSICID CIDPAR ON PAR.CODCID = CIDPAR.CODCID
        INNER JOIN TSIUFS UFSPAR ON UFSPAR.CODUF = CIDPAR.UF
        LEFT  JOIN TGFTPP PER ON PER.CODTIPPARC = PAR.CODTIPPARC
        INNER JOIN TGFITE ITE ON CAB.NUNOTA = ITE.NUNOTA
        INNER JOIN TGFPRO PRO ON ITE.CODPROD = PRO.CODPROD
        INNER JOIN TGFTOP TPO ON CAB.CODTIPOPER = TPO.CODTIPOPER AND CAB.DHTIPOPER = TPO.DHALTER
        INNER JOIN TGFGRU GRU ON PRO.CODGRUPOPROD = GRU.CODGRUPOPROD
        LEFT  JOIN TGFPAR USO ON CAB.AD_CLIENTEUSO = USO.CODPARC
        WHERE CAB.DTNEG BETWEEN '{safe_start}' AND '{safe_end}'
          AND CAB.STATUSNOTA = 'L'
          AND CAB.TIPMOV = 'V'
          AND ITE.CODCFO = 5102
          {filtro_vendedor}
        ) SUB
        ORDER BY SUB."Dt. Ent Sai" DESC, SUB."Nro Nota" DESC
        """
        
        # SQL Server TOP
        query = query.replace("SELECT * FROM (", "SELECT TOP 200 * FROM (", 1)
        return self.execute_query(query)

    # 2. COMPRAS (Baseado no XML, TIPMOV = 'C' para Compras)
    def get_compras(self, start_date: str, end_date: str, cod_fornecedor: Optional[str] = None) -> List[Dict[str, Any]]:
        safe_start = start_date.replace("'", "''")
        safe_end = end_date.replace("'", "''")
        
        filtro_forn = ""
        if cod_fornecedor:
            safe_forn = cod_fornecedor.replace("'", "''")
            filtro_forn = f"AND CAB.CODPARC = {safe_forn}"

        query = f"""
        SELECT 
            CAB.NUMNOTA AS NRO_NOTA,
            CAB.DTNEG AS DATA_NEGOCIACAO,
            PAR.RAZAOSOCIAL AS FORNECEDOR,
            PRO.DESCRPROD AS PRODUTO,
            ITE.QTDNEG AS QUANTIDADE,
            ITE.VLRTOT AS VALOR_TOTAL
        FROM TGFCAB CAB
        INNER JOIN TGFITE ITE ON CAB.NUNOTA = ITE.NUNOTA
        INNER JOIN TGFPRO PRO ON ITE.CODPROD = PRO.CODPROD
        INNER JOIN TGFPAR PAR ON CAB.CODPARC = PAR.CODPARC
        WHERE CAB.DTNEG BETWEEN '{safe_start}' AND '{safe_end}'
          AND CAB.TIPMOV = 'C' 
          AND CAB.STATUSNOTA = 'L'
          {filtro_forn}
        ORDER BY CAB.DTNEG DESC
        """
        query = query.replace("SELECT", "SELECT TOP 100", 1)
        return self.execute_query(query)

    # 3. PRODUTOS (Da TGFPRO)
    def get_produtos(self, busca: Optional[str] = None) -> List[Dict[str, Any]]:
        filtro = ""
        if busca:
            safe_busca = busca.replace("'", "''").upper()
            filtro = f"WHERE UPPER(DESCRPROD) LIKE '%{safe_busca}%' OR TO_CHAR(CODPROD) = '{safe_busca}'"
            
        query = f"""
        SELECT CODPROD, DESCRPROD, MARCA, NCM, REFERENCIA
        FROM TGFPRO
        {filtro}
        """
        query = query.replace("SELECT", "SELECT TOP 50", 1)
        return self.execute_query(query)

    # 4. PARCEIROS (Da TGFPAR)
    def get_parceiros(self, busca: Optional[str] = None, tipo: Optional[str] = None) -> List[Dict[str, Any]]:
        filtros = []
        if busca:
            safe_busca = busca.replace("'", "''").upper()
            filtros.append(f"(UPPER(RAZAOSOCIAL) LIKE '%{safe_busca}%' OR CGC_CPF LIKE '%{safe_busca}%')")
        if tipo == "cliente":
            filtros.append("CLIENTE = 'S'")
        elif tipo == "fornecedor":
            filtros.append("FORNECEDOR = 'S'")
            
        where_clause = "WHERE " + " AND ".join(filtros) if filtros else ""
        
        query = f"""
        SELECT CODPARC, RAZAOSOCIAL, CGC_CPF, CLIENTE, FORNECEDOR, ATIVO
        FROM TGFPAR
        {where_clause}
        """
        query = query.replace("SELECT", "SELECT TOP 50", 1)
        return self.execute_query(query)

    # 5. VENDEDORES (Da TGFVEN)
    def get_vendedores(self, busca: Optional[str] = None) -> List[Dict[str, Any]]:
        filtro = ""
        if busca:
            safe_busca = busca.replace("'", "''").upper()
            filtro = f"WHERE UPPER(APELIDO) LIKE '%{safe_busca}%'"
            
        query = f"""
        SELECT CODVEND, APELIDO, ATIVO
        FROM TGFVEN
        {filtro}
        """
        return self.execute_query(query)
