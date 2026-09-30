from fastapi import APIRouter, Query, Depends, HTTPException
from typing import Optional
from dependencies import get_sankhya_api
from services.sankhya_api import SankhyaAPI

router = APIRouter(prefix="/vendas", tags=["Vendas"])

@router.get("/")
def get_vendas(
    start_date: str = Query(..., description="Data Inicial (DD/MM/YYYY)"),
    end_date: str = Query(..., description="Data Final (DD/MM/YYYY)"),
    vendedor: Optional[str] = None,
    api: SankhyaAPI = Depends(get_sankhya_api)
):
    safe_start = start_date.replace("'", "''")
    safe_end = end_date.replace("'", "''")
    
    filtro_vendedor = ""
    if vendedor:
        safe_vend = vendedor.replace("'", "''")
        filtro_vendedor = f"AND CAB.CODVEND = {safe_vend}"

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
    
    query = query.replace("SELECT * FROM (", "SELECT TOP 200 * FROM (", 1)
    
    try:
        return api.execute_query(query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
