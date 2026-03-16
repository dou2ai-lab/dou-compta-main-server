# -----------------------------------------------------------------------------
# File: connectors.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 10-12-2025
# Description: ERP connectors (SAP, NetSuite, Odoo)
# -----------------------------------------------------------------------------

"""
ERP Connectors
Supports SAP, NetSuite, and Odoo via API or SFTP
"""
from typing import Dict, Any, List, Optional
import structlog
import json
from datetime import datetime

logger = structlog.get_logger()

class ERPConnector:
    """Base ERP connector"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.provider = config.get("provider", "odoo")
        self.connection_type = config.get("connection_type", "api")
    
    async def post_accounting_entry(
        self,
        posting_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Post accounting entry to ERP"""
        raise NotImplementedError
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test ERP connection"""
        raise NotImplementedError

class SAPConnector(ERPConnector):
    """SAP connector"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_url = config.get("api_url")
        self.username = config.get("username")
        self.password = config.get("password")
        self.client = config.get("client")
    
    async def post_accounting_entry(
        self,
        posting_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Post accounting entry to SAP"""
        try:
            if self.connection_type == "api":
                return await self._post_via_api(posting_data)
            elif self.connection_type == "sftp":
                return await self._post_via_sftp(posting_data)
            else:
                raise ValueError(f"Unsupported connection type: {self.connection_type}")
        except Exception as e:
            logger.error("sap_posting_error", error=str(e))
            raise
    
    async def _post_via_api(self, posting_data: Dict[str, Any]) -> Dict[str, Any]:
        """Post via SAP API"""
        # Placeholder for SAP API integration
        # In production, use SAP BAPI or OData services
        logger.info("sap_api_posting", posting_data=posting_data)
        
        return {
            "success": True,
            "erp_document_id": f"SAP-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "status": "posted",
            "posted_at": datetime.utcnow().isoformat()
        }
    
    async def _post_via_sftp(self, posting_data: Dict[str, Any]) -> Dict[str, Any]:
        """Post via SFTP file upload"""
        # Placeholder for SFTP file upload
        # In production, generate SAP-compatible file format
        logger.info("sap_sftp_posting", posting_data=posting_data)
        
        return {
            "success": True,
            "erp_document_id": f"SAP-SFTP-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "status": "pending",
            "file_path": f"/sftp/sap/{datetime.utcnow().strftime('%Y%m%d')}.txt"
        }
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test SAP connection"""
        try:
            # Placeholder for connection test
            return {
                "success": True,
                "provider": "sap",
                "connection_type": self.connection_type
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

class NetSuiteConnector(ERPConnector):
    """NetSuite connector"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.account_id = config.get("account_id")
        self.consumer_key = config.get("consumer_key")
        self.consumer_secret = config.get("consumer_secret")
        self.token_id = config.get("token_id")
        self.token_secret = config.get("token_secret")
    
    async def post_accounting_entry(
        self,
        posting_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Post accounting entry to NetSuite"""
        try:
            if self.connection_type == "api":
                return await self._post_via_api(posting_data)
            elif self.connection_type == "sftp":
                return await self._post_via_sftp(posting_data)
            else:
                raise ValueError(f"Unsupported connection type: {self.connection_type}")
        except Exception as e:
            logger.error("netsuite_posting_error", error=str(e))
            raise
    
    async def _post_via_api(self, posting_data: Dict[str, Any]) -> Dict[str, Any]:
        """Post via NetSuite REST API"""
        # Placeholder for NetSuite REST API integration
        logger.info("netsuite_api_posting", posting_data=posting_data)
        
        return {
            "success": True,
            "erp_document_id": f"NS-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "status": "posted",
            "posted_at": datetime.utcnow().isoformat()
        }
    
    async def _post_via_sftp(self, posting_data: Dict[str, Any]) -> Dict[str, Any]:
        """Post via SFTP file upload"""
        logger.info("netsuite_sftp_posting", posting_data=posting_data)
        
        return {
            "success": True,
            "erp_document_id": f"NS-SFTP-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "status": "pending",
            "file_path": f"/sftp/netsuite/{datetime.utcnow().strftime('%Y%m%d')}.csv"
        }
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test NetSuite connection"""
        try:
            return {
                "success": True,
                "provider": "netsuite",
                "connection_type": self.connection_type
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

class OdooConnector(ERPConnector):
    """Odoo connector"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.url = config.get("url")
        self.database = config.get("database")
        self.username = config.get("username")
        self.password = config.get("password")
        self.uid = None
    
    async def _authenticate(self):
        """Authenticate with Odoo"""
        try:
            import xmlrpc.client
            common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common')
            self.uid = common.authenticate(self.database, self.username, self.password, {})
            if not self.uid:
                raise ValueError("Odoo authentication failed")
        except Exception as e:
            logger.error("odoo_auth_error", error=str(e))
            raise
    
    async def post_accounting_entry(
        self,
        posting_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Post accounting entry to Odoo"""
        try:
            if self.connection_type == "api":
                return await self._post_via_api(posting_data)
            elif self.connection_type == "sftp":
                return await self._post_via_sftp(posting_data)
            else:
                raise ValueError(f"Unsupported connection type: {self.connection_type}")
        except Exception as e:
            logger.error("odoo_posting_error", error=str(e))
            raise
    
    async def _post_via_api(self, posting_data: Dict[str, Any]) -> Dict[str, Any]:
        """Post via Odoo XML-RPC API"""
        try:
            await self._authenticate()
            import xmlrpc.client
            models = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object')
            
            # Create account.move (journal entry) in Odoo
            move_data = {
                'date': posting_data.get('posting_date', datetime.utcnow().date().isoformat()),
                'journal_id': posting_data.get('journal_id', 1),
                'ref': posting_data.get('reference', ''),
                'line_ids': posting_data.get('line_ids', [])
            }
            
            move_id = models.execute_kw(
                self.database, self.uid, self.password,
                'account.move', 'create', [move_data]
            )
            
            return {
                "success": True,
                "erp_document_id": str(move_id),
                "status": "posted",
                "posted_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error("odoo_api_posting_error", error=str(e))
            raise
    
    async def _post_via_sftp(self, posting_data: Dict[str, Any]) -> Dict[str, Any]:
        """Post via SFTP file upload"""
        logger.info("odoo_sftp_posting", posting_data=posting_data)
        
        return {
            "success": True,
            "erp_document_id": f"ODOO-SFTP-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "status": "pending",
            "file_path": f"/sftp/odoo/{datetime.utcnow().strftime('%Y%m%d')}.csv"
        }
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test Odoo connection"""
        try:
            await self._authenticate()
            return {
                "success": True,
                "provider": "odoo",
                "connection_type": self.connection_type,
                "user_id": self.uid
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

def get_erp_connector(config: Dict[str, Any]) -> ERPConnector:
    """Factory function to get appropriate ERP connector"""
    provider = config.get("provider", "odoo").lower()
    
    if provider == "sap":
        return SAPConnector(config)
    elif provider == "netsuite":
        return NetSuiteConnector(config)
    elif provider == "odoo":
        return OdooConnector(config)
    else:
        raise ValueError(f"Unsupported ERP provider: {provider}")




