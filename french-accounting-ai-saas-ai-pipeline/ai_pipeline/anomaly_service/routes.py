# -----------------------------------------------------------------------------
# File: routes.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 10-12-2025
# Description: API routes for anomaly detection service
# -----------------------------------------------------------------------------

"""
Anomaly Detection Service Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Dict, Any
import structlog

from common.database import get_db
from common.models import User
from services.auth.dependencies import get_current_user, get_user_permissions, get_user_roles
from .service import AnomalyDetectionService
from .schemas import (
    ExpenseAnalysisResponse,
    ExpenseAnalysisWithExplanation,
    RiskDashboardResponse,
    HighRiskEmployee,
    HighRiskMerchant,
    SuspiciousTransaction,
    RepeatedViolation,
    MerchantProfile,
    MerchantSpendAnalysis,
    AuditSampleRequest,
    AuditSampleResponse,
    ModelRefinementResponse
)

logger = structlog.get_logger()
router = APIRouter()

async def require_audit_permission(current_user: User, db: AsyncSession):
    """Check if user has audit permissions or Admin role."""
    permissions = await get_user_permissions(current_user, db)
    if "audit:read" in permissions:
        return
    roles = await get_user_roles(current_user, db)
    if roles and any(str(r).lower() == "admin" for r in roles):
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Audit access required"
    )

@router.post("/analyze/{expense_id}", response_model=ExpenseAnalysisWithExplanation)
async def analyze_expense(
    expense_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Analyze a single expense for anomalies and risk with LLM explanations"""
    await require_audit_permission(current_user, db)
    
    try:
        service = AnomalyDetectionService(db, str(current_user.tenant_id))
        result = await service.analyze_expense(expense_id)
        await db.commit()
        return ExpenseAnalysisWithExplanation(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        await db.rollback()
        logger.error("analyze_expense_error", expense_id=expense_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to analyze expense")

@router.post("/jobs/run-monitoring")
async def run_monitoring_job(
    limit: int = Query(500, ge=1, le=2000),
    lookback_days: int = Query(90, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Run continuous monitoring: profile spend, update risk scores for expenses/employees/merchants (5.2.1)."""
    await require_audit_permission(current_user, db)
    try:
        service = AnomalyDetectionService(db, str(current_user.tenant_id))
        result = await service.run_batch_analysis_and_persist(limit=limit, lookback_days=lookback_days)
        await db.commit()
        logger.info("monitoring_job_completed", tenant_id=str(current_user.tenant_id), **result)
        return {"success": True, "message": "Monitoring job completed", "result": result}
    except Exception as e:
        await db.rollback()
        logger.error("monitoring_job_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to run monitoring job")

@router.post("/train")
async def train_model(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Train the anomaly detection model"""
    await require_audit_permission(current_user, db)
    
    try:
        service = AnomalyDetectionService(db, str(current_user.tenant_id))
        success = await service.train_model()
        
        if success:
            return {"success": True, "message": "Model trained successfully"}
        else:
            raise HTTPException(
                status_code=400,
                detail="Failed to train model. Insufficient data or training error."
            )
    except Exception as e:
        logger.error("train_model_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to train model")

@router.get("/dashboard", response_model=RiskDashboardResponse)
async def get_risk_dashboard(
    limit_employees: int = Query(10, ge=1, le=50, alias="limitEmployees"),
    limit_merchants: int = Query(10, ge=1, le=50, alias="limitMerchants"),
    limit_transactions: int = Query(50, ge=1, le=200, alias="limitTransactions"),
    min_risk_score: float = Query(0.7, ge=0.0, le=1.0, alias="minRiskScore"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get comprehensive risk dashboard data"""
    await require_audit_permission(current_user, db)
    
    try:
        service = AnomalyDetectionService(db, str(current_user.tenant_id))
        
        # Ensure model is trained
        if not service._model_trained:
            await service.train_model()
        
        # Get all dashboard data
        high_risk_employees = await service.get_high_risk_employees(
            limit=limit_employees,
            min_risk_score=min_risk_score
        )
        
        high_risk_merchants = await service.get_high_risk_merchants(
            limit=limit_merchants,
            min_risk_score=min_risk_score
        )
        
        suspicious_transactions = await service.get_suspicious_transactions(
            limit=limit_transactions,
            min_risk_score=min_risk_score
        )
        
        repeated_violations = await service.get_repeated_violations(limit=20)
        
        # Calculate summary statistics
        summary = {
            "total_high_risk_employees": len(high_risk_employees),
            "total_high_risk_merchants": len(high_risk_merchants),
            "total_suspicious_transactions": len(suspicious_transactions),
            "total_repeated_violations": len(repeated_violations),
            "total_high_risk_amount": sum(
                emp['total_amount'] for emp in high_risk_employees
            )
        }
        
        return RiskDashboardResponse(
            high_risk_employees=[HighRiskEmployee(**emp) for emp in high_risk_employees],
            high_risk_merchants=[HighRiskMerchant(**merch) for merch in high_risk_merchants],
            suspicious_transactions=[SuspiciousTransaction(**tx) for tx in suspicious_transactions],
            repeated_violations=[RepeatedViolation(**viol) for viol in repeated_violations],
            summary=summary
        )
        
    except Exception as e:
        logger.error("risk_dashboard_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to generate risk dashboard")

@router.get("/employees/high-risk", response_model=List[HighRiskEmployee])
async def get_high_risk_employees(
    limit: int = Query(10, ge=1, le=50),
    min_risk_score: float = Query(0.7, ge=0.0, le=1.0, alias="minRiskScore"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get list of high-risk employees"""
    await require_audit_permission(current_user, db)
    
    try:
        service = AnomalyDetectionService(db, str(current_user.tenant_id))
        employees = await service.get_high_risk_employees(limit, min_risk_score)
        return [HighRiskEmployee(**emp) for emp in employees]
    except Exception as e:
        logger.error("high_risk_employees_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get high-risk employees")

@router.get("/merchants/high-risk", response_model=List[HighRiskMerchant])
async def get_high_risk_merchants(
    limit: int = Query(10, ge=1, le=50),
    min_risk_score: float = Query(0.7, ge=0.0, le=1.0, alias="minRiskScore"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get list of high-risk merchants"""
    await require_audit_permission(current_user, db)
    
    try:
        service = AnomalyDetectionService(db, str(current_user.tenant_id))
        merchants = await service.get_high_risk_merchants(limit, min_risk_score)
        return [HighRiskMerchant(**merch) for merch in merchants]
    except Exception as e:
        logger.error("high_risk_merchants_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get high-risk merchants")

@router.get("/transactions/suspicious", response_model=List[SuspiciousTransaction])
async def get_suspicious_transactions(
    limit: int = Query(50, ge=1, le=200),
    min_risk_score: float = Query(0.7, ge=0.0, le=1.0, alias="minRiskScore"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get list of suspicious transactions"""
    await require_audit_permission(current_user, db)
    
    try:
        service = AnomalyDetectionService(db, str(current_user.tenant_id))
        transactions = await service.get_suspicious_transactions(limit, min_risk_score)
        return [SuspiciousTransaction(**tx) for tx in transactions]
    except Exception as e:
        logger.error("suspicious_transactions_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get suspicious transactions")

@router.get("/violations/repeated", response_model=List[RepeatedViolation])
async def get_repeated_violations(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get employees with repeated policy violations"""
    await require_audit_permission(current_user, db)
    
    try:
        service = AnomalyDetectionService(db, str(current_user.tenant_id))
        violations = await service.get_repeated_violations(limit)
        return [RepeatedViolation(**viol) for viol in violations]
    except Exception as e:
        logger.error("repeated_violations_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get repeated violations")

# Phase 15 & 16 Routes

@router.post("/refine", response_model=ModelRefinementResponse)
async def refine_model(
    days_back: int = Query(30, ge=7, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Refine the anomaly detection model using real data"""
    await require_audit_permission(current_user, db)
    
    try:
        service = AnomalyDetectionService(db, str(current_user.tenant_id))
        result = await service.model_refiner.refine_model(days_back=days_back)
        return ModelRefinementResponse(**result)
    except Exception as e:
        logger.error("model_refinement_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to refine model")

@router.post("/tune-contamination", response_model=ModelRefinementResponse)
async def tune_contamination(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Automatically tune contamination parameter"""
    await require_audit_permission(current_user, db)
    
    try:
        service = AnomalyDetectionService(db, str(current_user.tenant_id))
        result = await service.model_refiner.adaptive_contamination_tuning()
        return ModelRefinementResponse(**result)
    except Exception as e:
        logger.error("contamination_tuning_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to tune contamination")

@router.get("/merchants/{merchant_name}", response_model=MerchantProfile)
async def get_merchant_profile(
    merchant_name: str,
    days_back: int = Query(90, ge=7, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed profile for a merchant"""
    await require_audit_permission(current_user, db)
    
    try:
        service = AnomalyDetectionService(db, str(current_user.tenant_id))
        profile = await service.merchant_profiler.get_merchant_profile(merchant_name, days_back)
        return MerchantProfile(**profile)
    except Exception as e:
        logger.error("merchant_profile_error", merchant_name=merchant_name, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get merchant profile")

@router.get("/merchants", response_model=List[Dict[str, Any]])
async def get_top_merchants(
    limit: int = Query(20, ge=1, le=100),
    days_back: int = Query(90, ge=7, le=365),
    sort_by: str = Query("total_amount", pattern="^(total_amount|count|avg_amount)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get top merchants by various metrics"""
    await require_audit_permission(current_user, db)
    
    try:
        service = AnomalyDetectionService(db, str(current_user.tenant_id))
        merchants = await service.merchant_profiler.get_top_merchants(limit, days_back, sort_by)
        return merchants
    except Exception as e:
        logger.error("top_merchants_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get top merchants")

@router.get("/merchants/analysis/spend", response_model=MerchantSpendAnalysis)
async def get_merchant_spend_analysis(
    days_back: int = Query(90, ge=7, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get overall merchant spend analysis"""
    await require_audit_permission(current_user, db)
    
    try:
        service = AnomalyDetectionService(db, str(current_user.tenant_id))
        analysis = await service.merchant_profiler.get_merchant_spend_analysis(days_back)
        return MerchantSpendAnalysis(**analysis)
    except Exception as e:
        logger.error("spend_analysis_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get spend analysis")

@router.post("/audit/sample", response_model=AuditSampleResponse)
async def get_audit_sample(
    request: AuditSampleRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get risk-based audit sample"""
    await require_audit_permission(current_user, db)
    
    try:
        service = AnomalyDetectionService(db, str(current_user.tenant_id))
        sample = await service.risk_sampler.select_audit_sample(
            sample_size=request.sample_size,
            min_risk_score=request.min_risk_score,
            strategy=request.strategy
        )
        return AuditSampleResponse(**sample)
    except Exception as e:
        logger.error("audit_sampling_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to generate audit sample")

