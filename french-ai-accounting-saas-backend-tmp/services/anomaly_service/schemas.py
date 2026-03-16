# -----------------------------------------------------------------------------
# File: schemas.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 10-12-2025
# Description: Pydantic schemas for anomaly detection service
# -----------------------------------------------------------------------------

"""
Pydantic schemas for Anomaly Detection Service
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from decimal import Decimal

class ExpenseAnalysisResponse(BaseModel):
    """Expense analysis response"""
    expense_id: str
    is_anomaly: bool
    anomaly_score: float
    risk_score: float
    risk_level: str
    risk_factors: Dict[str, float]
    features: Dict[str, Any]
    anomaly_reasons: Optional[List[str]] = None

class HighRiskEmployee(BaseModel):
    """High risk employee response"""
    user_id: str
    email: str
    name: str
    avg_risk_score: float
    expense_count: int
    high_risk_count: int
    anomaly_count: int
    total_amount: float

class HighRiskMerchant(BaseModel):
    """High risk merchant response"""
    merchant_name: str
    avg_risk_score: float
    expense_count: int
    high_risk_count: int
    anomaly_count: int
    total_amount: float
    unique_employees: int

class SuspiciousTransaction(BaseModel):
    """Suspicious transaction response"""
    expense_id: str
    amount: float
    currency: str
    merchant_name: Optional[str]
    category: Optional[str]
    expense_date: str
    user_id: str
    user_email: str
    user_name: str
    risk_score: float
    risk_level: str
    is_anomaly: bool
    anomaly_score: float

class RepeatedViolation(BaseModel):
    """Repeated violation response"""
    user_id: str
    email: str
    name: str
    violation_count: int
    last_violation: Optional[str]

class RiskDashboardResponse(BaseModel):
    """Risk dashboard response"""
    high_risk_employees: List[HighRiskEmployee]
    high_risk_merchants: List[HighRiskMerchant]
    suspicious_transactions: List[SuspiciousTransaction]
    repeated_violations: List[RepeatedViolation]
    summary: Dict[str, Any]

class AnalyzeExpenseRequest(BaseModel):
    """Request to analyze an expense"""
    expense_id: str

class AnomalyExplanation(BaseModel):
    """Anomaly explanation response"""
    behavioural_patterns: Dict[str, Any]
    vat_errors: Dict[str, Any]
    policy_inconsistencies: Dict[str, Any]
    summary: str

class ExpenseAnalysisWithExplanation(ExpenseAnalysisResponse):
    """Expense analysis with LLM explanations"""
    explanations: AnomalyExplanation

class MerchantProfile(BaseModel):
    """Merchant profile response"""
    merchant_name: str
    exists: bool
    statistics: Dict[str, Any]
    patterns: Dict[str, Any]
    approval_metrics: Dict[str, Any]
    employees: List[Dict[str, Any]]
    risk_indicators: Dict[str, Any]

class MerchantSpendAnalysis(BaseModel):
    """Merchant spend analysis response"""
    period_days: int
    summary: Dict[str, Any]
    top_merchants: List[Dict[str, Any]]
    concentration: Dict[str, Any]

class AuditSampleRequest(BaseModel):
    """Request for audit sample"""
    sample_size: int = Field(50, ge=1, le=500)
    min_risk_score: float = Field(0.4, ge=0.0, le=1.0)
    strategy: str = Field("risk_weighted", pattern="^(risk_weighted|stratified|random)$")

class AuditSampleResponse(BaseModel):
    """Audit sample response"""
    success: bool
    strategy: str
    sample_size: int
    total_candidates: int
    filtered_candidates: int
    min_risk_score: float
    sample: List[Dict[str, Any]]
    statistics: Dict[str, Any]

class ModelRefinementResponse(BaseModel):
    """Model refinement response"""
    success: bool
    message: Optional[str] = None
    samples_used: Optional[int] = None
    previous_metrics: Optional[Dict[str, Any]] = None
    new_metrics: Optional[Dict[str, Any]] = None
    improvement: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None

