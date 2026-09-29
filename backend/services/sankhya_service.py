import requests
import xml.etree.ElementTree as ET
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class SankhyaService:
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.jsessionid = None

    def login(self) -> str:
        """Authenticates with Sankhya ERP and returns the JSESSIONID."""
        url = f"{self.base_url}/mge/workspace.mge?nomologin={self.username}&password={self.password}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            
            # Simple parsing for JSESSIONID (Actual implementation might need XML parsing depending on response)
            if "JSESSIONID" in response.cookies:
                self.jsessionid = response.cookies["JSESSIONID"]
                return self.jsessionid
            
            # If returned in XML body
            try:
                root = ET.fromstring(response.content)
                jsessionid_node = root.find(".//jsessionid")
                if jsessionid_node is not None:
                    self.jsessionid = jsessionid_node.text
                    return self.jsessionid
            except ET.ParseError:
                pass
                
            raise Exception("Failed to retrieve JSESSIONID")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Login failed: {e}")
            raise

    def get_sales(self, start_date: str, end_date: str, brand_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Queries sales data from Sankhya via mge/DbExplorerSP.mac@executeQuery.
        Applies a brand filter if provided.
        """
        if not self.jsessionid:
            self.login()

        url = f"{self.base_url}/mge/DbExplorerSP.mac@executeQuery?JSESSIONID={self.jsessionid}"
        
        # Example Query (Adjust based on actual Sankhya database schema)
        query = f"""
        SELECT 
            ITE.CODPROD, PRO.DESCRPROD, PRO.MARCA, ITE.VLRUNIT, CAB.DTNEG
        FROM 
            TGFCAB CAB
        INNER JOIN TGFITE ITE ON CAB.NUNOTA = ITE.NUNOTA
        INNER JOIN TGFPRO PRO ON ITE.CODPROD = PRO.CODPROD
        WHERE CAB.DTNEG BETWEEN '{start_date}' AND '{end_date}'
        """
        
        if brand_filter:
            query += f" AND PRO.MARCA = '{brand_filter}'"
            
        xml_body = f"""
        <serviceRequest serviceName="DbExplorerSP.executeQuery">
            <requestBody>
                <sql><![CDATA[{query}]]></sql>
            </requestBody>
        </serviceRequest>
        """
        
        headers = {'Content-Type': 'text/xml;charset=UTF-8'}
        
        try:
            response = requests.post(url, data=xml_body.encode('utf-8'), headers=headers)
            response.raise_for_status()
            
            # Parse XML Response
            root = ET.fromstring(response.content)
            status = root.attrib.get('status', '0')
            if status != '1':
                error_msg = root.find(".//statusMessage")
                msg = error_msg.text if error_msg is not None else "Unknown error"
                raise Exception(f"Sankhya API Error: {msg}")
                
            records = []
            # Extract fields and records (This depends heavily on actual XML structure returned by executeQuery)
            # Typically returns <fields><field name="..."/></fields> and <records><record><f>val</f>...</record></records>
            # Simplified parsing:
            
            return records
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch sales: {e}")
            raise
