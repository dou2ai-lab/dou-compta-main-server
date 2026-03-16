# -----------------------------------------------------------------------------
# File: model_refiner.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 10-12-2025
# Description: ML model refinement using real data feedback
# -----------------------------------------------------------------------------

"""
Model Refinement Service
Refines anomaly detection model using real data and feedback
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from common.models import Expense
from .anomaly_detector import AnomalyDetector
from .feature_engineering import FeatureEngineeringPipeline
from .config import settings
import structlog

logger = structlog.get_logger()

class ModelRefiner:
    """Refine ML model using real data feedback"""
    
    def __init__(
        self,
        db: AsyncSession,
        tenant_id: str,
        anomaly_detector: AnomalyDetector,
        feature_pipeline: FeatureEngineeringPipeline
    ):
        self.db = db
        self.tenant_id = tenant_id
        self.anomaly_detector = anomaly_detector
        self.feature_pipeline = feature_pipeline
        self.refinement_history: List[Dict[str, Any]] = []
    
    async def refine_model(
        self,
        use_recent_data: bool = True,
        days_back: int = 30,
        min_samples: int = 50
    ) -> Dict[str, Any]:
        """
        Refine the model using recent real data
        Returns refinement metrics and improvements
        """
        try:
            logger.info("starting_model_refinement", tenant_id=self.tenant_id)
            
            # Get recent expenses for refinement
            if use_recent_data:
                cutoff_date = datetime.utcnow() - timedelta(days=days_back)
                
                result = await self.db.execute(
                    select(Expense).where(
                        and_(
                            Expense.tenant_id == self.tenant_id,
                            Expense.expense_date >= cutoff_date,
                            Expense.deleted_at.is_(None)
                        )
                    )
                )
                recent_expenses = result.scalars().all()
                
                if len(recent_expenses) < min_samples:
                    return {
                        "success": False,
                        "message": f"Insufficient data. Need at least {min_samples} samples, got {len(recent_expenses)}"
                    }
                
                # Build dataset from recent expenses
                df = await self.feature_pipeline.build_training_dataset()
            else:
                # Use all available data
                df = await self.feature_pipeline.build_training_dataset()
            
            if df.empty or len(df) < min_samples:
                return {
                    "success": False,
                    "message": f"Insufficient data for refinement. Got {len(df)} samples."
                }
            
            # Store previous model metrics
            previous_metrics = self._get_model_metrics()
            
            # Retrain model with new data
            success = self.anomaly_detector.train(df)
            
            if not success:
                return {
                    "success": False,
                    "message": "Failed to retrain model"
                }
            
            # Get new model metrics
            new_metrics = self._get_model_metrics()
            
            # Calculate improvement
            improvement = self._calculate_improvement(previous_metrics, new_metrics)
            
            # Store refinement record
            refinement_record = {
                "timestamp": datetime.utcnow().isoformat(),
                "samples_used": len(df),
                "previous_metrics": previous_metrics,
                "new_metrics": new_metrics,
                "improvement": improvement
            }
            self.refinement_history.append(refinement_record)
            
            logger.info(
                "model_refinement_complete",
                samples=len(df),
                improvement=improvement
            )
            
            return {
                "success": True,
                "samples_used": len(df),
                "previous_metrics": previous_metrics,
                "new_metrics": new_metrics,
                "improvement": improvement,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("model_refinement_error", error=str(e))
            return {
                "success": False,
                "message": f"Error during refinement: {str(e)}"
            }
    
    def _get_model_metrics(self) -> Dict[str, Any]:
        """Get current model metrics"""
        if not self.anomaly_detector.is_trained:
            return {"trained": False}
        
        model_info = self.anomaly_detector.get_model_info()
        return {
            "trained": True,
            "contamination": model_info.get("contamination", 0),
            "n_estimators": model_info.get("n_estimators", 0),
            "features": model_info.get("features", 0)
        }
    
    def _calculate_improvement(
        self,
        previous: Dict[str, Any],
        current: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate improvement metrics"""
        if not previous.get("trained") or not current.get("trained"):
            return {"improvement_score": 0.0, "message": "Cannot calculate - model not trained"}
        
        # Simple improvement calculation
        # In production, you'd use validation metrics, precision, recall, etc.
        improvement_score = 0.0
        
        if current.get("features", 0) > previous.get("features", 0):
            improvement_score += 0.1
        
        return {
            "improvement_score": improvement_score,
            "message": "Model refined successfully" if improvement_score > 0 else "No significant improvement"
        }
    
    async def adaptive_contamination_tuning(self) -> Dict[str, Any]:
        """
        Automatically tune contamination parameter based on actual anomaly rate
        """
        try:
            # Get recent expenses and analyze them
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            
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
            
            if len(expenses) < 50:
                return {
                    "success": False,
                    "message": "Insufficient data for contamination tuning"
                }
            
            # Analyze actual anomaly rate (based on policy violations, rejections, etc.)
            # This is a simplified version - in production, use more sophisticated metrics
            from common.models import PolicyViolation
            
            violation_result = await self.db.execute(
                select(PolicyViolation).join(
                    Expense, PolicyViolation.expense_id == Expense.id
                ).where(
                    and_(
                        Expense.tenant_id == self.tenant_id,
                        Expense.expense_date >= cutoff_date
                    )
                )
            )
            violations = violation_result.scalars().all()
            
            # Calculate actual anomaly rate
            actual_anomaly_rate = len(violations) / len(expenses) if expenses else 0.0
            actual_anomaly_rate = min(0.3, max(0.05, actual_anomaly_rate))  # Clamp between 5% and 30%
            
            # Update contamination if significantly different
            current_contamination = settings.ISOLATION_FOREST_CONTAMINATION
            if abs(actual_anomaly_rate - current_contamination) > 0.05:
                # Retrain with new contamination
                self.anomaly_detector.contamination = actual_anomaly_rate
                
                df = await self.feature_pipeline.build_training_dataset()
                if not df.empty:
                    self.anomaly_detector.train(df)
                
                return {
                    "success": True,
                    "previous_contamination": current_contamination,
                    "new_contamination": actual_anomaly_rate,
                    "actual_anomaly_rate": actual_anomaly_rate,
                    "message": f"Contamination tuned from {current_contamination:.2f} to {actual_anomaly_rate:.2f}"
                }
            
            return {
                "success": True,
                "contamination": current_contamination,
                "actual_anomaly_rate": actual_anomaly_rate,
                "message": "Contamination already optimal"
            }
            
        except Exception as e:
            logger.error("contamination_tuning_error", error=str(e))
            return {
                "success": False,
                "message": f"Error during tuning: {str(e)}"
            }
    
    def get_refinement_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get refinement history"""
        return self.refinement_history[-limit:]




