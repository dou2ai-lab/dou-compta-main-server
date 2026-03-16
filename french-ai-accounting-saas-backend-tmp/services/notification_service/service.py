# -----------------------------------------------------------------------------
# File: service.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 01-12-2025
# Description: Email notification service
# -----------------------------------------------------------------------------

"""
Email notification service
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from uuid import UUID
from datetime import datetime
import structlog
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

from common.models import EmailNotification, User, ExpenseReport, Expense

logger = structlog.get_logger()

class EmailNotificationService:
    """Service for sending email notifications"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.smtp_host = os.getenv("SMTP_HOST", "localhost")
        self.smtp_port = int(os.getenv("SMTP_PORT", "25"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("FROM_EMAIL", "noreply@dou-expense.ai")
        self.enabled = os.getenv("EMAIL_NOTIFICATIONS_ENABLED", "false").lower() == "true"
    
    async def send_approval_request_notification(
        self,
        report: ExpenseReport,
        approver: User
    ) -> Optional[EmailNotification]:
        """Send approval request notification to approver"""
        if not self.enabled:
            logger.info("email_notifications_disabled", skipping=True)
            return None
        
        try:
            # Get submitter
            submitter_result = await self.db.execute(
                select(User).where(User.id == report.submitted_by)
            )
            submitter = submitter_result.scalar_one_or_none()
            
            if not submitter:
                logger.warning("submitter_not_found", report_id=str(report.id))
                return None
            
            subject = f"Expense Report Approval Request: {report.report_number}"
            body = f"""
Dear {approver.first_name or approver.email},

You have received an expense report approval request.

Report Details:
- Report Number: {report.report_number}
- Submitted By: {submitter.first_name} {submitter.last_name} ({submitter.email})
- Total Amount: {report.total_amount} {report.currency}
- Expense Count: {report.expense_count}
- Report Type: {report.report_type}

{f'Period: {report.period_start_date} to {report.period_end_date}' if report.period_start_date else ''}
{f'Trip: {report.trip_name} - {report.trip_destination}' if report.trip_name else ''}

Please review and approve or reject this expense report.

This is an automated notification from Dou Expense & Audit AI.
"""
            
            notification = await self._create_notification(
                tenant_id=report.tenant_id,
                recipient_id=approver.id,
                notification_type="approval_request",
                subject=subject,
                body=body,
                entity_type="expense_report",
                entity_id=report.id
            )
            
            # Send email
            await self._send_email(
                to_email=approver.email,
                subject=subject,
                body=body,
                notification=notification
            )
            
            return notification
            
        except Exception as e:
            logger.error("approval_request_notification_failed", error=str(e), exc_info=True)
            return None
    
    async def send_approval_approved_notification(
        self,
        report: ExpenseReport
    ) -> Optional[EmailNotification]:
        """Send approval approved notification to submitter"""
        if not self.enabled:
            return None
        
        try:
            submitter_result = await self.db.execute(
                select(User).where(User.id == report.submitted_by)
            )
            submitter = submitter_result.scalar_one_or_none()
            
            if not submitter:
                return None
            
            subject = f"Expense Report Approved: {report.report_number}"
            body = f"""
Dear {submitter.first_name or submitter.email},

Your expense report has been approved.

Report Details:
- Report Number: {report.report_number}
- Total Amount: {report.total_amount} {report.currency}
- Approved At: {report.approved_at}

{f'Approval Notes: {report.approval_notes}' if report.approval_notes else ''}

This is an automated notification from Dou Expense & Audit AI.
"""
            
            notification = await self._create_notification(
                tenant_id=report.tenant_id,
                recipient_id=submitter.id,
                notification_type="approval_approved",
                subject=subject,
                body=body,
                entity_type="expense_report",
                entity_id=report.id
            )
            
            await self._send_email(
                to_email=submitter.email,
                subject=subject,
                body=body,
                notification=notification
            )
            
            return notification
            
        except Exception as e:
            logger.error("approval_approved_notification_failed", error=str(e), exc_info=True)
            return None
    
    async def send_approval_rejected_notification(
        self,
        report: ExpenseReport
    ) -> Optional[EmailNotification]:
        """Send approval rejected notification to submitter"""
        if not self.enabled:
            return None
        
        try:
            submitter_result = await self.db.execute(
                select(User).where(User.id == report.submitted_by)
            )
            submitter = submitter_result.scalar_one_or_none()
            
            if not submitter:
                return None
            
            subject = f"Expense Report Rejected: {report.report_number}"
            body = f"""
Dear {submitter.first_name or submitter.email},

Your expense report has been rejected.

Report Details:
- Report Number: {report.report_number}
- Total Amount: {report.total_amount} {report.currency}
- Rejected At: {report.rejected_at}

Rejection Reason: {report.rejection_reason}

Please review and resubmit if necessary.

This is an automated notification from Dou Expense & Audit AI.
"""
            
            notification = await self._create_notification(
                tenant_id=report.tenant_id,
                recipient_id=submitter.id,
                notification_type="approval_rejected",
                subject=subject,
                body=body,
                entity_type="expense_report",
                entity_id=report.id
            )
            
            await self._send_email(
                to_email=submitter.email,
                subject=subject,
                body=body,
                notification=notification
            )
            
            return notification
            
        except Exception as e:
            logger.error("approval_rejected_notification_failed", error=str(e), exc_info=True)
            return None
    
    async def _create_notification(
        self,
        tenant_id: UUID,
        recipient_id: UUID,
        notification_type: str,
        subject: str,
        body: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[UUID] = None
    ) -> EmailNotification:
        """Create notification record"""
        notification = EmailNotification(
            tenant_id=tenant_id,
            recipient_id=recipient_id,
            notification_type=notification_type,
            subject=subject,
            body=body,
            entity_type=entity_type,
            entity_id=entity_id,
            status="pending"
        )
        
        self.db.add(notification)
        await self.db.flush()
        
        return notification
    
    async def _send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        notification: EmailNotification
    ):
        """Send email via SMTP"""
        try:
            msg = MIMEMultipart()
            msg["From"] = self.from_email
            msg["To"] = to_email
            msg["Subject"] = subject
            
            msg.attach(MIMEText(body, "plain"))
            
            # Send email
            if self.smtp_host and self.smtp_host != "localhost":
                with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                    if self.smtp_user and self.smtp_password:
                        server.login(self.smtp_user, self.smtp_password)
                    server.send_message(msg)
            
            # Update notification
            notification.status = "sent"
            notification.sent_at = datetime.utcnow()
            await self.db.flush()
            
            logger.info("email_sent", notification_id=str(notification.id), to_email=to_email)
            
        except Exception as e:
            notification.status = "failed"
            notification.error_message = str(e)
            await self.db.flush()
            
            logger.error("email_send_failed", error=str(e), notification_id=str(notification.id))

    async def send_expense_submission_notification(
        self,
        expense_id: UUID,
        submitter_id: UUID,
        approver_id: UUID
    ) -> Optional[EmailNotification]:
        """Send expense submission notification to manager/approver"""
        if not self.enabled:
            logger.info("email_notifications_disabled", skipping=True)
            return None
        
        try:
            # Get expense
            expense_result = await self.db.execute(
                select(Expense).where(Expense.id == expense_id)
            )
            expense = expense_result.scalar_one_or_none()
            
            if not expense:
                return None
            
            # Get submitter and approver
            submitter_result = await self.db.execute(
                select(User).where(User.id == submitter_id)
            )
            submitter = submitter_result.scalar_one_or_none()
            
            approver_result = await self.db.execute(
                select(User).where(User.id == approver_id)
            )
            approver = approver_result.scalar_one_or_none()
            
            if not submitter or not approver:
                return None
            
            subject = f"Expense Approval Request: {expense.merchant_name or 'Expense'}"
            body = f"""
Dear {approver.first_name or approver.email},

You have received an expense approval request.

Expense Details:
- Amount: {expense.amount} {expense.currency}
- Submitted By: {submitter.first_name} {submitter.last_name} ({submitter.email})
- Date: {expense.expense_date}
- Category: {expense.category or 'N/A'}
- Merchant: {expense.merchant_name or 'N/A'}
- Description: {expense.description or 'N/A'}

Please review and approve or reject this expense.

This is an automated notification from Dou Expense & Audit AI.
"""
            
            notification = await self._create_notification(
                tenant_id=expense.tenant_id,
                recipient_id=approver.id,
                notification_type="expense_approval_request",
                subject=subject,
                body=body,
                entity_type="expense",
                entity_id=expense.id
            )
            
            await self._send_email(
                to_email=approver.email,
                subject=subject,
                body=body,
                notification=notification
            )
            
            return notification
            
        except Exception as e:
            logger.error("expense_submission_notification_failed", error=str(e), exc_info=True)
            return None
    
    async def send_expense_approval_notification(
        self,
        expense_id: UUID,
        submitter_id: UUID,
        approver_id: UUID,
        approved: bool
    ) -> Optional[EmailNotification]:
        """Send expense approval/rejection notification to submitter"""
        if not self.enabled:
            return None
        
        try:
            expense_result = await self.db.execute(
                select(Expense).where(Expense.id == expense_id)
            )
            expense = expense_result.scalar_one_or_none()
            
            if not expense:
                return None
            
            submitter_result = await self.db.execute(
                select(User).where(User.id == submitter_id)
            )
            submitter = submitter_result.scalar_one_or_none()
            
            if not submitter:
                return None
            
            if approved:
                subject = f"Expense Approved: {expense.merchant_name or 'Expense'}"
                body = f"""
Dear {submitter.first_name or submitter.email},

Your expense has been approved.

Expense Details:
- Amount: {expense.amount} {expense.currency}
- Date: {expense.expense_date}
- Merchant: {expense.merchant_name or 'N/A'}
- Approved At: {expense.approved_at}

This is an automated notification from Dou Expense & Audit AI.
"""
                notification_type = "expense_approved"
            else:
                subject = f"Expense Rejected: {expense.merchant_name or 'Expense'}"
                body = f"""
Dear {submitter.first_name or submitter.email},

Your expense has been rejected.

Expense Details:
- Amount: {expense.amount} {expense.currency}
- Date: {expense.expense_date}
- Merchant: {expense.merchant_name or 'N/A'}

Rejection Reason: {expense.rejection_reason or 'No reason provided'}

Please review and resubmit if necessary.

This is an automated notification from Dou Expense & Audit AI.
"""
                notification_type = "expense_rejected"
            
            notification = await self._create_notification(
                tenant_id=expense.tenant_id,
                recipient_id=submitter.id,
                notification_type=notification_type,
                subject=subject,
                body=body,
                entity_type="expense",
                entity_id=expense.id
            )
            
            await self._send_email(
                to_email=submitter.email,
                subject=subject,
                body=body,
                notification=notification
            )
            
            return notification
            
        except Exception as e:
            logger.error("expense_approval_notification_failed", error=str(e), exc_info=True)
            return None


# Alias for backward compatibility
NotificationService = EmailNotificationService








