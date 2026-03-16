# -----------------------------------------------------------------------------
# File: sepa_builder.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 10-12-2025
# Description: SEPA export builder for reimbursement automation
# -----------------------------------------------------------------------------

"""
SEPA Export Builder
Generates SEPA XML files for reimbursement automation
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from datetime import datetime, date
from decimal import Decimal
import structlog
import xml.etree.ElementTree as ET
from xml.dom import minidom

from .models import SEPATransaction, SEPAFile
from common.models import Expense, User

logger = structlog.get_logger()

class SEPABuilder:
    """SEPA file builder for reimbursement automation"""
    
    def __init__(self, db: AsyncSession, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
    
    async def create_sepa_file(
        self,
        expense_ids: List[str],
        creditor_iban: str,
        creditor_bic: Optional[str] = None,
        creditor_name: Optional[str] = None,
        execution_date: Optional[date] = None,
        created_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create SEPA file for reimbursement"""
        try:
            # Get expenses
            result = await self.db.execute(
                select(Expense).where(
                    and_(
                        Expense.id.in_(expense_ids),
                        Expense.tenant_id == self.tenant_id,
                        Expense.deleted_at.is_(None),
                        Expense.status == "approved"
                    )
                )
            )
            expenses = result.scalars().all()
            
            if not expenses:
                raise ValueError("No approved expenses found")
            
            # Get creditor info from tenant or user
            if not creditor_name:
                creditor_name = await self._get_creditor_name()
            if not creditor_bic:
                creditor_bic = await self._get_creditor_bic(creditor_iban)
            
            # Create SEPA file record
            sepa_file = SEPAFile(
                tenant_id=self.tenant_id,
                file_name=f"SEPA-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.xml",
                transaction_count=len(expenses),
                total_amount=sum(float(e.amount) for e in expenses),
                status="pending",
                created_by=created_by
            )
            
            self.db.add(sepa_file)
            await self.db.flush()
            
            # Create transactions
            transactions = []
            for expense in expenses:
                # Get employee/user info for debtor
                debtor_info = await self._get_debtor_info(expense.submitted_by)
                
                transaction = SEPATransaction(
                    tenant_id=self.tenant_id,
                    transaction_id=f"TXN-{expense.id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    creditor_name=creditor_name,
                    creditor_iban=creditor_iban,
                    creditor_bic=creditor_bic,
                    debtor_name=debtor_info.get("name", "Employee"),
                    debtor_iban=debtor_info.get("iban", ""),
                    debtor_bic=debtor_info.get("bic"),
                    amount=expense.amount,
                    currency=expense.currency or "EUR",
                    execution_date=execution_date or date.today(),
                    remittance_info=f"Reimbursement EXP-{expense.id}",
                    expense_ids=[str(expense.id)],
                    status="pending",
                    sepa_file_id=sepa_file.id,
                    created_by=created_by
                )
                
                self.db.add(transaction)
                transactions.append(transaction)
            
            await self.db.flush()
            
            # Generate SEPA XML
            xml_content = await self._generate_sepa_xml(sepa_file, transactions)
            
            # Update file with path
            sepa_file.file_path = f"/tmp/sepa/{sepa_file.file_name}"
            sepa_file.file_size = len(xml_content.encode('utf-8'))
            sepa_file.status = "generated"
            
            await self.db.commit()
            
            return {
                "success": True,
                "file_id": str(sepa_file.id),
                "file_name": sepa_file.file_name,
                "file_path": sepa_file.file_path,
                "transaction_count": len(transactions),
                "total_amount": float(sepa_file.total_amount),
                "xml_content": xml_content
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error("create_sepa_file_error", error=str(e))
            raise
    
    async def _generate_sepa_xml(
        self,
        sepa_file: SEPAFile,
        transactions: List[SEPATransaction]
    ) -> str:
        """Generate SEPA XML file (pain.001.001.03 format)"""
        try:
            # Create root element
            root = ET.Element("Document", xmlns="urn:iso:std:iso:20022:tech:xsd:pain.001.001.03")
            
            # CstmrCdtTrfInitn (Customer Credit Transfer Initiation)
            cstmr_cdt_trf_initn = ET.SubElement(root, "CstmrCdtTrfInitn")
            
            # Group Header
            grp_hdr = ET.SubElement(cstmr_cdt_trf_initn, "GrpHdr")
            msg_id = ET.SubElement(grp_hdr, "MsgId")
            msg_id.text = f"MSG-{sepa_file.id}"
            cre_dt_tm = ET.SubElement(grp_hdr, "CreDtTm")
            cre_dt_tm.text = datetime.utcnow().isoformat()
            nb_of_txs = ET.SubElement(grp_hdr, "NbOfTxs")
            nb_of_txs.text = str(len(transactions))
            ctrl_sum = ET.SubElement(grp_hdr, "CtrlSum")
            ctrl_sum.text = f"{sepa_file.total_amount:.2f}"
            initg_pty = ET.SubElement(grp_hdr, "InitgPty")
            nm = ET.SubElement(initg_pty, "Nm")
            nm.text = transactions[0].creditor_name if transactions else "Company"
            
            # Payment Information
            pmt_inf = ET.SubElement(cstmr_cdt_trf_initn, "PmtInf")
            pmt_inf_id = ET.SubElement(pmt_inf, "PmtInfId")
            pmt_inf_id.text = f"PMT-{sepa_file.id}"
            pmt_mtd = ET.SubElement(pmt_inf, "PmtMtd")
            pmt_mtd.text = "TRF"  # Transfer
            nb_of_txs_pmt = ET.SubElement(pmt_inf, "NbOfTxs")
            nb_of_txs_pmt.text = str(len(transactions))
            ctrl_sum_pmt = ET.SubElement(pmt_inf, "CtrlSum")
            ctrl_sum_pmt.text = f"{sepa_file.total_amount:.2f}"
            pmt_tp_inf = ET.SubElement(pmt_inf, "PmtTpInf")
            svc_lvl = ET.SubElement(pmt_tp_inf, "SvcLvl")
            cd = ET.SubElement(svc_lvl, "Cd")
            cd.text = "SEPA"
            reqd_exctn_dt = ET.SubElement(pmt_inf, "ReqdExctnDt")
            reqd_exctn_dt.text = transactions[0].execution_date.isoformat() if transactions else date.today().isoformat()
            
            # Debtor Account
            dbtr = ET.SubElement(pmt_inf, "Dbtr")
            dbtr_nm = ET.SubElement(dbtr, "Nm")
            dbtr_nm.text = transactions[0].creditor_name if transactions else "Company"
            dbtr_acct = ET.SubElement(pmt_inf, "DbtrAcct")
            dbtr_acct_id = ET.SubElement(dbtr_acct, "Id")
            dbtr_acct_iban = ET.SubElement(dbtr_acct_id, "IBAN")
            dbtr_acct_iban.text = transactions[0].creditor_iban if transactions else ""
            dbtr_acct_agt = ET.SubElement(pmt_inf, "DbtrAgt")
            fin_instn_id = ET.SubElement(dbtr_acct_agt, "FinInstnId")
            if transactions and transactions[0].creditor_bic:
                bic = ET.SubElement(fin_instn_id, "BIC")
                bic.text = transactions[0].creditor_bic
            
            # Credit Transfer Transaction Information
            for transaction in transactions:
                cdt_trf_tx_inf = ET.SubElement(pmt_inf, "CdtTrfTxInf")
                pmt_id = ET.SubElement(cdt_trf_tx_inf, "PmtId")
                end_to_end_id = ET.SubElement(pmt_id, "EndToEndId")
                end_to_end_id.text = transaction.transaction_id
                amt = ET.SubElement(cdt_trf_tx_inf, "Amt")
                instd_amt = ET.SubElement(amt, "InstdAmt", Ccy=transaction.currency)
                instd_amt.text = f"{transaction.amount:.2f}"
                cdtr_agt = ET.SubElement(cdt_trf_tx_inf, "CdtrAgt")
                fin_instn_id_cdtr = ET.SubElement(cdtr_agt, "FinInstnId")
                if transaction.debtor_bic:
                    bic_cdtr = ET.SubElement(fin_instn_id_cdtr, "BIC")
                    bic_cdtr.text = transaction.debtor_bic
                cdtr = ET.SubElement(cdt_trf_tx_inf, "Cdtr")
                cdtr_nm = ET.SubElement(cdtr, "Nm")
                cdtr_nm.text = transaction.debtor_name
                cdtr_acct = ET.SubElement(cdt_trf_tx_inf, "CdtrAcct")
                cdtr_acct_id = ET.SubElement(cdtr_acct, "Id")
                cdtr_acct_iban = ET.SubElement(cdtr_acct_id, "IBAN")
                cdtr_acct_iban.text = transaction.debtor_iban
                rmt_inf = ET.SubElement(cdt_trf_tx_inf, "RmtInf")
                ustrd = ET.SubElement(rmt_inf, "Ustrd")
                ustrd.text = transaction.remittance_info
            
            # Format XML
            xml_str = ET.tostring(root, encoding='utf-8', method='xml')
            dom = minidom.parseString(xml_str)
            pretty_xml = dom.toprettyxml(indent="  ")
            
            return pretty_xml
            
        except Exception as e:
            logger.error("generate_sepa_xml_error", error=str(e))
            raise
    
    async def _get_creditor_name(self) -> str:
        """Get creditor name from tenant"""
        # Placeholder - get from tenant settings
        return "Company Name"
    
    async def _get_creditor_bic(self, iban: str) -> Optional[str]:
        """Get BIC from IBAN or lookup"""
        # Placeholder - in production, lookup BIC from IBAN
        return None
    
    async def _get_debtor_info(self, user_id: str) -> Dict[str, Any]:
        """Get debtor (employee) information"""
        try:
            result = await self.db.execute(
                select(User).where(
                    and_(
                        User.id == user_id,
                        User.tenant_id == self.tenant_id
                    )
                )
            )
            user = result.scalar_one_or_none()
            
            if user:
                # In production, get IBAN/BIC from user profile or bank account settings
                return {
                    "name": f"{user.first_name} {user.last_name}" if user.first_name else user.email,
                    "iban": "",  # Get from user profile
                    "bic": None  # Get from user profile
                }
            
            return {"name": "Employee", "iban": "", "bic": None}
            
        except Exception as e:
            logger.error("get_debtor_info_error", error=str(e))
            return {"name": "Employee", "iban": "", "bic": None}




