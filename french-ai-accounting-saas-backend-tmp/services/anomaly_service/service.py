# -----------------------------------------------------------------------------
# File: service.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 10-12-2025
# Description: Anomaly detection and risk scoring service
# -----------------------------------------------------------------------------

"""
Anomaly Detection and Risk Scoring Service
Main service layer that orchestrates feature engineering, anomaly detection, and risk scoring
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from common.models import Expense, User, PolicyViolation, RiskScore
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from decimal import Decimal
import structlog

from .feature_engineering import FeatureEngineeringPipeline
from .anomaly_detector import AnomalyDetector
from .risk_scorer import RiskScorer
from .model_refiner import ModelRefiner
from .llm_explainer import LLMAnomalyExplainer
from .merchant_profiler import MerchantProfiler
from .risk_sampler import RiskBasedSampler
from .anomaly_rules import get_rule_based_reasons
from .config import settings

logger = structlog.get_logger()

class AnomalyDetectionService:
    """Main service for anomaly detection and risk scoring"""
    
    def __init__(self, db: AsyncSession, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self.feature_pipeline = FeatureEngineeringPipeline(
            db, tenant_id, settings.LOOKBACK_DAYS
        )
        self.anomaly_detector = AnomalyDetector(
            contamination=settings.ISOLATION_FOREST_CONTAMINATION,
            n_estimators=settings.ISOLATION_FOREST_N_ESTIMATORS
        )
        self.risk_scorer = RiskScorer(
            db, tenant_id,
            high_threshold=settings.RISK_SCORE_THRESHOLD_HIGH,
            medium_threshold=settings.RISK_SCORE_THRESHOLD_MEDIUM
        )
        self.model_refiner = ModelRefiner(db, tenant_id, self.anomaly_detector, self.feature_pipeline)
        self.llm_explainer = LLMAnomalyExplainer(db, tenant_id)
        self.merchant_profiler = MerchantProfiler(db, tenant_id)
        self.risk_sampler = RiskBasedSampler(db, tenant_id)
        self._model_trained = False
    
    async def train_model(self) -> bool:
        """Train the anomaly detection model on historical data"""
        try:
            logger.info("training_anomaly_detector", tenant_id=self.tenant_id)
            
            # Build training dataset
            df = await self.feature_pipeline.build_training_dataset()
            
            if df.empty or len(df) < settings.MIN_EXPENSES_FOR_BASELINE:
                logger.warning(
                    "insufficient_training_data",
                    rows=len(df),
                    required=settings.MIN_EXPENSES_FOR_BASELINE
                )
                return False
            
            # Train model
            success = self.anomaly_detector.train(df)
            self._model_trained = success
            
            if success:
                logger.info("anomaly_detector_trained_successfully", samples=len(df))
            else:
                logger.error("anomaly_detector_training_failed")
            
            return success
            
        except Exception as e:
            logger.error("model_training_error", error=str(e))
            return False
    
    async def analyze_expense(self, expense_id: str) -> Dict[str, Any]:
        """Analyze a single expense for anomalies and calculate risk score"""
        try:
            # Get expense
            result = await self.db.execute(
                select(Expense).where(
                    and_(
                        Expense.id == expense_id,
                        Expense.tenant_id == self.tenant_id,
                        Expense.deleted_at.is_(None)
                    )
                )
            )
            expense = result.scalar_one_or_none()
            
            if not expense:
                raise ValueError(f"Expense {expense_id} not found")
            
            # Ensure model is trained
            if not self._model_trained:
                await self.train_model()
            
            # Extract features
            features = await self.feature_pipeline.extract_expense_features(expense)
            
            # Detect anomaly (ML)
            is_ml_anomaly, anomaly_score = self.anomaly_detector.predict(features)
            
            # Rule-based reason codes
            rule_reasons = await get_rule_based_reasons(self.db, expense, is_ml_anomaly)
            is_anomaly = is_ml_anomaly or len(rule_reasons) > 0
            
            # Calculate risk score
            risk_result = await self.risk_scorer.calculate_risk_score(
                expense, anomaly_score, is_anomaly
            )
            risk_score_val = risk_result['risk_score']
            
            # Persist to expense (5.2.2)
            expense.risk_score_line = Decimal(str(round(risk_score_val, 4)))
            expense.is_anomaly = is_anomaly
            expense.anomaly_reasons = rule_reasons
            await self.db.flush()
            
            return {
                'expense_id': str(expense_id),
                'is_anomaly': is_anomaly,
                'anomaly_score': anomaly_score,
                'anomaly_reasons': rule_reasons,
                'risk_score': risk_score_val,
                'risk_level': risk_result['risk_level'],
                'risk_factors': risk_result['risk_factors'],
                'features': features
            }
            
        except Exception as e:
            logger.error("expense_analysis_error", expense_id=expense_id, error=str(e))
            raise

    async def _upsert_risk_score(
        self,
        entity_type: str,
        entity_id: str,
        risk_score: float,
        meta_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Upsert risk_scores table for employee or merchant (5.2.1)."""
        r = await self.db.execute(
            select(RiskScore).where(
                and_(
                    RiskScore.tenant_id == self.tenant_id,
                    RiskScore.entity_type == entity_type,
                    RiskScore.entity_id == entity_id,
                )
            )
        )
        row = r.scalar_one_or_none()
        val = Decimal(str(round(risk_score, 4)))
        if row:
            row.risk_score = val
            row.meta_data = meta_data or {}
        else:
            self.db.add(
                RiskScore(
                    tenant_id=self.tenant_id,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    risk_score=val,
                    meta_data=meta_data or {},
                )
            )
        await self.db.flush()

    async def run_batch_analysis_and_persist(
        self,
        limit: int = 500,
        lookback_days: int = 90,
    ) -> Dict[str, Any]:
        """
        Run anomaly + risk on recent expenses, persist to expenses and risk_scores.
        Used by continuous monitoring job (5.2.1).
        """
        cutoff = datetime.utcnow().date() - timedelta(days=lookback_days)
        result = await self.db.execute(
            select(Expense).where(
                and_(
                    Expense.tenant_id == self.tenant_id,
                    Expense.expense_date >= cutoff,
                    Expense.deleted_at.is_(None),
                )
            ).order_by(Expense.updated_at.desc()).limit(limit)
        )
        expenses = result.scalars().all()
        if not self._model_trained and expenses:
            await self.train_model()
        processed = 0
        employee_totals: Dict[str, List[float]] = {}
        merchant_totals: Dict[str, List[float]] = {}
        for exp in expenses:
            try:
                analysis = await self.analyze_expense(str(exp.id))
                risk = analysis["risk_score"]
                emp_id = str(exp.submitted_by)
                merchant = (exp.merchant_name or "").strip() or "_unknown_"
                employee_totals.setdefault(emp_id, []).append(risk)
                merchant_totals.setdefault(merchant, []).append(risk)
                processed += 1
            except Exception as e:
                logger.warning("batch_analysis_skip", expense_id=str(exp.id), error=str(e))
        for emp_id, scores in employee_totals.items():
            avg = sum(scores) / len(scores)
            await self._upsert_risk_score("employee", emp_id, avg, {"expense_count": len(scores)})
        for merchant, scores in merchant_totals.items():
            if merchant == "_unknown_":
                continue
            avg = sum(scores) / len(scores)
            await self._upsert_risk_score("merchant", merchant, avg, {"expense_count": len(scores)})
        return {"processed": processed, "employees_updated": len(employee_totals), "merchants_updated": len([m for m in merchant_totals if m != "_unknown_"])}

    async def get_high_risk_employees(
        self,
        limit: int = 10,
        min_risk_score: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Get employees with high risk scores"""
        try:
            # Get all expenses with risk scores
            cutoff_date = datetime.utcnow() - timedelta(days=90)
            
            result = await self.db.execute(
                select(Expense).where(
                    and_(
                        Expense.tenant_id == self.tenant_id,
                        Expense.expense_date >= cutoff_date,
                        Expense.deleted_at.is_(None)
                    )
                )
            )
            expenses = result.scalars().all()
            
            # Analyze each expense and aggregate by employee
            employee_risks = {}
            
            for expense in expenses:
                try:
                    analysis = await self.analyze_expense(str(expense.id))
                    user_id = str(expense.submitted_by)
                    
                    if user_id not in employee_risks:
                        employee_risks[user_id] = {
                            'user_id': user_id,
                            'expense_count': 0,
                            'total_risk_score': 0.0,
                            'high_risk_count': 0,
                            'anomaly_count': 0,
                            'total_amount': 0.0
                        }
                    
                    employee_risks[user_id]['expense_count'] += 1
                    employee_risks[user_id]['total_risk_score'] += analysis['risk_score']
                    if analysis['risk_score'] >= min_risk_score:
                        employee_risks[user_id]['high_risk_count'] += 1
                    if analysis['is_anomaly']:
                        employee_risks[user_id]['anomaly_count'] += 1
                    employee_risks[user_id]['total_amount'] += float(expense.amount)
                    
                except Exception as e:
                    logger.error("employee_risk_calculation_error", expense_id=str(expense.id), error=str(e))
                    continue
            
            # Calculate averages and get user info
            high_risk_employees = []
            for user_id, data in employee_risks.items():
                avg_risk = data['total_risk_score'] / data['expense_count']
                if avg_risk >= min_risk_score:
                    # Get user info
                    user_result = await self.db.execute(
                        select(User).where(User.id == user_id)
                    )
                    user = user_result.scalar_one_or_none()
                    
                    high_risk_employees.append({
                        'user_id': user_id,
                        'email': user.email if user else 'Unknown',
                        'name': f"{user.first_name} {user.last_name}" if user else 'Unknown',
                        'avg_risk_score': avg_risk,
                        'expense_count': data['expense_count'],
                        'high_risk_count': data['high_risk_count'],
                        'anomaly_count': data['anomaly_count'],
                        'total_amount': data['total_amount']
                    })
            
            # Sort by risk score and limit
            high_risk_employees.sort(key=lambda x: x['avg_risk_score'], reverse=True)
            return high_risk_employees[:limit]
            
        except Exception as e:
            logger.error("high_risk_employees_error", error=str(e))
            return []
    
    async def get_high_risk_merchants(
        self,
        limit: int = 10,
        min_risk_score: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Get merchants with high risk scores"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=90)
            
            result = await self.db.execute(
                select(Expense).where(
                    and_(
                        Expense.tenant_id == self.tenant_id,
                        Expense.merchant_name.isnot(None),
                        Expense.expense_date >= cutoff_date,
                        Expense.deleted_at.is_(None)
                    )
                )
            )
            expenses = result.scalars().all()
            
            merchant_risks = {}
            
            for expense in expenses:
                try:
                    analysis = await self.analyze_expense(str(expense.id))
                    merchant = expense.merchant_name
                    
                    if merchant not in merchant_risks:
                        merchant_risks[merchant] = {
                            'merchant_name': merchant,
                            'expense_count': 0,
                            'total_risk_score': 0.0,
                            'high_risk_count': 0,
                            'anomaly_count': 0,
                            'total_amount': 0.0,
                            'unique_employees': set()
                        }
                    
                    merchant_risks[merchant]['expense_count'] += 1
                    merchant_risks[merchant]['total_risk_score'] += analysis['risk_score']
                    merchant_risks[merchant]['unique_employees'].add(str(expense.submitted_by))
                    if analysis['risk_score'] >= min_risk_score:
                        merchant_risks[merchant]['high_risk_count'] += 1
                    if analysis['is_anomaly']:
                        merchant_risks[merchant]['anomaly_count'] += 1
                    merchant_risks[merchant]['total_amount'] += float(expense.amount)
                    
                except Exception as e:
                    logger.error("merchant_risk_calculation_error", expense_id=str(expense.id), error=str(e))
                    continue
            
            high_risk_merchants = []
            for merchant, data in merchant_risks.items():
                avg_risk = data['total_risk_score'] / data['expense_count']
                if avg_risk >= min_risk_score:
                    high_risk_merchants.append({
                        'merchant_name': merchant,
                        'avg_risk_score': avg_risk,
                        'expense_count': data['expense_count'],
                        'high_risk_count': data['high_risk_count'],
                        'anomaly_count': data['anomaly_count'],
                        'total_amount': data['total_amount'],
                        'unique_employees': len(data['unique_employees'])
                    })
            
            high_risk_merchants.sort(key=lambda x: x['avg_risk_score'], reverse=True)
            return high_risk_merchants[:limit]
            
        except Exception as e:
            logger.error("high_risk_merchants_error", error=str(e))
            return []
    
    async def get_suspicious_transactions(
        self,
        limit: int = 50,
        min_risk_score: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Get suspicious transactions (high risk or anomalies)"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=90)
            
            result = await self.db.execute(
                select(Expense).where(
                    and_(
                        Expense.tenant_id == self.tenant_id,
                        Expense.expense_date >= cutoff_date,
                        Expense.deleted_at.is_(None)
                    )
                ).order_by(Expense.expense_date.desc()).limit(limit * 3)  # Get more to filter
            )
            expenses = result.scalars().all()
            
            suspicious = []
            
            for expense in expenses:
                try:
                    analysis = await self.analyze_expense(str(expense.id))
                    
                    if analysis['risk_score'] >= min_risk_score or analysis['is_anomaly']:
                        # Get user info
                        user_result = await self.db.execute(
                            select(User).where(User.id == expense.submitted_by)
                        )
                        user = user_result.scalar_one_or_none()
                        
                        suspicious.append({
                            'expense_id': str(expense.id),
                            'amount': float(expense.amount),
                            'currency': expense.currency,
                            'merchant_name': expense.merchant_name,
                            'category': expense.category,
                            'expense_date': expense.expense_date.isoformat(),
                            'user_id': str(expense.submitted_by),
                            'user_email': user.email if user else 'Unknown',
                            'user_name': f"{user.first_name} {user.last_name}" if user else 'Unknown',
                            'risk_score': analysis['risk_score'],
                            'risk_level': analysis['risk_level'],
                            'is_anomaly': analysis['is_anomaly'],
                            'anomaly_score': analysis['anomaly_score']
                        })
                        
                        if len(suspicious) >= limit:
                            break
                            
                except Exception as e:
                    logger.error("suspicious_transaction_error", expense_id=str(expense.id), error=str(e))
                    continue
            
            return suspicious
            
        except Exception as e:
            logger.error("suspicious_transactions_error", error=str(e))
            return []
    
    async def get_repeated_violations(
        self,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get employees with repeated policy violations"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=90)
            
            # Get violations grouped by user (via expense)
            result = await self.db.execute(
                select(
                    Expense.submitted_by,
                    func.count(PolicyViolation.id).label('violation_count'),
                    func.max(PolicyViolation.created_at).label('last_violation')
                ).join(
                    PolicyViolation, Expense.id == PolicyViolation.expense_id
                ).where(
                    and_(
                        Expense.tenant_id == self.tenant_id,
                        PolicyViolation.created_at >= cutoff_date
                    )
                ).group_by(Expense.submitted_by).having(
                    func.count(PolicyViolation.id) >= 2
                ).order_by(func.count(PolicyViolation.id).desc()).limit(limit)
            )
            violations = result.all()
            
            repeated_violations = []
            
            for user_id, count, last_violation in violations:
                # Get user info
                user_result = await self.db.execute(
                    select(User).where(User.id == user_id)
                )
                user = user_result.scalar_one_or_none()
                
                repeated_violations.append({
                    'user_id': str(user_id),
                    'email': user.email if user else 'Unknown',
                    'name': f"{user.first_name} {user.last_name}" if user else 'Unknown',
                    'violation_count': count,
                    'last_violation': last_violation.isoformat() if last_violation else None
                })
            
            return repeated_violations
            
        except Exception as e:
            logger.error("repeated_violations_error", error=str(e))
            return []

