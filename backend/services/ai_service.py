import joblib
import numpy as np
import pandas as pd
from typing import Dict, Tuple
from math import ceil, exp
from utils.load_models import (
    load_model_vehicle,
    load_model_bank,
    load_model_ecommerce,
    load_model_eth
)
from utils.transforms import (
    transform_vehicle_fraud_data,
    transform_bank_fraud_data,
    transform_ecommerce_fraud_data,
    transform_ethereum_fraud_data
)


class FraudDetectionService:
    """
    Single-model fraud detection service.
    """
    
    def __init__(self):
        """Load all 4 models and their feature lists."""
        self.models = {
            "vehicle": load_model_vehicle(),
            "bank": load_model_bank(),
            "ecommerce": load_model_ecommerce(),
            "ethereum": load_model_eth()
        }
        self.transforms = {
            "vehicle": transform_vehicle_fraud_data,
            "bank": transform_bank_fraud_data,
            "ecommerce": transform_ecommerce_fraud_data,
            "ethereum": transform_ethereum_fraud_data
        }
    
    def detect_fraud(self, transaction_data: Dict, transaction_type: str) -> Dict:
        """
        Detect fraud for a single transaction.
        Returns only the fraud score (0 or 100) and status.
        """
        if transaction_type not in self.models:
            raise ValueError(f"Unknown transaction type: {transaction_type}")
        
        try:
            # 1. Unpack model and expected feature list
            model, expected_features = self.models[transaction_type]
            transform_fn = self.transforms[transaction_type]
            
            # 2. Convert to DataFrame
            df = pd.DataFrame([transaction_data])
            
            # 3. Transform data WITHOUT feature selection (get all transformed columns)
            transformed_data = transform_fn(df, selected_features=None)
            
            # 4. Reorder/select columns to match model's expected features
            if expected_features is not None:
                # Add missing features as 0
                for feature in expected_features:
                    if feature not in transformed_data.columns:
                        transformed_data[feature] = 0
                
                # Select only expected features in the EXACT order
                transformed_data = transformed_data[expected_features]
            
            # 5. Get probability prediction (continuous score between 0 and 1)
            # predict_proba returns [[prob_class_0, prob_class_1]]
            # We want the probability of fraud (class 1), which is index [:, 1]
            fraud_probability = model.predict_proba(transformed_data)[0, 1]
            
            # 6. Convert probability to score (0-100 continuous scale)
            # This gives a more robust and granular fraud score
            calculate_score = lambda p: (
                (p / 0.75) * 50 if p < 0.75 else 
                50 + ((p - 0.75) / 0.10) * 30 if p < 0.85 else 
                80 + ((p - 0.85) / 0.15) * 20
                )


            fraud_score = ceil(calculate_score(fraud_probability))
            
            
            return {
                "fraud_score": fraud_score,
                "transaction_type": transaction_type,
                "success": True
            }
        
        except Exception as e:
            print(f"Error in detect_fraud for {transaction_type}: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "fraud_score": 0,
                "transaction_type": transaction_type,
                "success": False,
                "error": str(e)
            }


# Global service instance
_service = None


def initialize_service():
    """Initialize fraud detection service."""
    global _service
    _service = FraudDetectionService()


def get_service() -> FraudDetectionService:
    """Get or initialize the fraud detection service."""
    global _service
    if _service is None:
        initialize_service()
    return _service


def detect_fraud(transaction_data: Dict, transaction_type: str) -> Dict:
    """
    Main entry point for fraud detection.
    """
    service = get_service()
    return service.detect_fraud(transaction_data, transaction_type)