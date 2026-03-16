# -----------------------------------------------------------------------------
# File: anomaly_detector.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 10-12-2025
# Description: Anomaly detection using Isolation Forest and statistical methods
# -----------------------------------------------------------------------------

"""
Anomaly Detection Engine
Uses Isolation Forest and statistical methods to detect anomalies
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from typing import Dict, Any, Tuple, Optional
import pickle
import structlog

logger = structlog.get_logger()

class AnomalyDetector:
    """Anomaly detection using Isolation Forest"""
    
    def __init__(
        self,
        contamination: float = 0.1,
        n_estimators: int = 100,
        random_state: int = 42
    ):
        self.contamination = contamination
        self.n_estimators = n_estimators
        self.random_state = random_state
        self.model: Optional[IsolationForest] = None
        self.scaler: Optional[StandardScaler] = None
        self.feature_columns: Optional[list] = None
        self.is_trained = False
    
    def train(self, df: pd.DataFrame) -> bool:
        """Train the anomaly detection model"""
        if df.empty or len(df) < 10:
            logger.warning("insufficient_data_for_training", rows=len(df))
            return False
        
        try:
            # Select numeric features
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            # Remove expense_id if present
            if 'expense_id' in numeric_cols:
                numeric_cols.remove('expense_id')
            
            if not numeric_cols:
                logger.warning("no_numeric_features")
                return False
            
            self.feature_columns = numeric_cols
            X = df[numeric_cols].fillna(0)
            
            # Scale features
            self.scaler = StandardScaler()
            X_scaled = self.scaler.fit_transform(X)
            
            # Train Isolation Forest
            self.model = IsolationForest(
                contamination=self.contamination,
                n_estimators=self.n_estimators,
                random_state=self.random_state,
                n_jobs=-1
            )
            self.model.fit(X_scaled)
            
            self.is_trained = True
            logger.info("anomaly_detector_trained", features=len(numeric_cols), samples=len(df))
            return True
            
        except Exception as e:
            logger.error("anomaly_detector_training_error", error=str(e))
            return False
    
    def predict(self, features: Dict[str, Any]) -> Tuple[bool, float]:
        """
        Predict if expense is an anomaly
        Returns: (is_anomaly, anomaly_score)
        """
        if not self.is_trained or self.model is None or self.scaler is None:
            logger.warning("model_not_trained")
            return False, 0.0
        
        try:
            # Convert features to array
            feature_vector = []
            for col in self.feature_columns:
                value = features.get(col, 0)
                if pd.isna(value) or value is None:
                    value = 0
                feature_vector.append(float(value))
            
            X = np.array([feature_vector])
            X_scaled = self.scaler.transform(X)
            
            # Predict
            prediction = self.model.predict(X_scaled)[0]
            anomaly_score = self.model.score_samples(X_scaled)[0]
            
            # Convert to boolean (IsolationForest returns -1 for anomaly, 1 for normal)
            is_anomaly = prediction == -1
            
            # Normalize score to 0-1 range (higher = more anomalous)
            # Isolation Forest scores are negative for anomalies, positive for normal
            # We invert and normalize
            normalized_score = 1.0 / (1.0 + np.exp(anomaly_score))
            
            return is_anomaly, float(normalized_score)
            
        except Exception as e:
            logger.error("anomaly_prediction_error", error=str(e))
            return False, 0.0
    
    def batch_predict(self, df: pd.DataFrame) -> pd.DataFrame:
        """Predict anomalies for a batch of expenses"""
        if not self.is_trained or self.model is None or self.scaler is None:
            logger.warning("model_not_trained")
            return df
        
        try:
            if self.feature_columns is None:
                return df
            
            X = df[self.feature_columns].fillna(0)
            X_scaled = self.scaler.transform(X)
            
            predictions = self.model.predict(X_scaled)
            scores = self.model.score_samples(X_scaled)
            
            df['is_anomaly'] = predictions == -1
            df['anomaly_score'] = 1.0 / (1.0 + np.exp(scores))
            
            return df
            
        except Exception as e:
            logger.error("batch_prediction_error", error=str(e))
            return df
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the trained model"""
        if not self.is_trained:
            return {"trained": False}
        
        return {
            "trained": True,
            "contamination": self.contamination,
            "n_estimators": self.n_estimators,
            "features": len(self.feature_columns) if self.feature_columns else 0,
            "feature_columns": self.feature_columns
        }




