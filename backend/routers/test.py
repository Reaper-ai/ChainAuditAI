from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
import pandas as pd
from datetime import datetime
import random
from core.database import SessionLocal
from models.fraud_log import FraudLog
from services.ai_service import detect_fraud, initialize_service
from services.chain_service import log_fraud_on_chain

router = APIRouter(prefix="/test", tags=["Testing & Fraud Detection"])

# Initialize service on startup
initialize_service()


# ============= Input Schemas =============

class TestRequest(BaseModel):
    """
    Request to test fraud detection.
    """
    transaction_type: str  # "vehicle", "bank", "ecommerce", "ethereum"
    fraud_label: str       # "fraud" or "non-fraud"
    num_samples: int = 1   # Added this field to fix the AttributeError


# ============= Output Schemas =============

class TestResultItem(BaseModel):
    fraud_score: int
    expected_fraud_label: Optional[str] = None
    database_id: Optional[int] = None
    blockchain_tx: Optional[str] = None


class TestResponse(BaseModel):
    transaction_type: str
    fraud_label: str
    total_samples: int
    results: List[TestResultItem]


# ============= Helper Functions =============

def load_test_data(transaction_type: str) -> pd.DataFrame:
    """Load appropriate test data CSV."""
    file_mapping = {
        "vehicle": "data/test_data/vehicle_test_data.csv",
        "bank": "data/test_data/bank_test_data.csv",
        "ecommerce": "data/test_data/ecommerce_test_data.csv",
        "ethereum": "data/test_data/ethereum_test_data.csv"
    }
    
    filepath = file_mapping.get(transaction_type)
    if not filepath:
        raise ValueError(f"Unknown transaction type: {transaction_type}")
    
    try:
        return pd.read_csv(filepath)
    except FileNotFoundError:
        raise FileNotFoundError(f"Test data not found: {filepath}")


def get_fraud_column(transaction_type: str) -> str:
    """Get fraud column name for transaction type."""
    fraud_col_mapping = {
        "vehicle": "FraudFound_P",
        "bank": "fraud_bool",
        "ecommerce": "Is Fraudulent",
        "ethereum": "Fraud"
    }
    return fraud_col_mapping.get(transaction_type, "fraud_label")


def get_random_subset(df: pd.DataFrame, fraud_label: str, n_samples: int = 1) -> List[Dict]:
    """Get random subset of fraud or non-fraud rows."""
    fraud_col = None
    # Dynamic column finder
    for col in df.columns:
        if 'fraud' in col.lower() or 'fraudulent' in col.lower():
            fraud_col = col
            break
    
    if not fraud_col:
        # Fallback
        fraud_col = get_fraud_column("vehicle") 

    # Filter based on label (1/0 or "1"/"0")
    if fraud_label == "fraud":
        subset_df = df[(df[fraud_col] == 1) | (df[fraud_col] == '1')]
    else:
        subset_df = df[(df[fraud_col] == 0) | (df[fraud_col] == '0')]
    
    # Random sample
    if len(subset_df) < n_samples:
        selected = subset_df
    else:
        selected = subset_df.sample(n=n_samples, random_state=None)
    
    return [row.to_dict() for _, row in selected.iterrows()]


# ============= Endpoints =============

@router.post("/run-test", response_model=TestResponse)
def run_fraud_test(request: TestRequest):
    """
    Run fraud detection test on random rows from test data.
    Defaults to 1 sample if not specified.
    """
    # Use the requested sample size or default to 1
    num_samples = request.num_samples if request.num_samples else 1
    
    valid_types = ["vehicle", "bank", "ecommerce", "ethereum"]
    if request.transaction_type not in valid_types:
        raise HTTPException(status_code=400, detail="Invalid transaction_type")
    
    try:
        # Step 1: Load test data
        df = load_test_data(request.transaction_type)
        
        # Step 2: Get random rows
        random_rows = get_random_subset(df, request.fraud_label, n_samples=num_samples)
        
        if not random_rows:
             return TestResponse(
                transaction_type=request.transaction_type,
                fraud_label=request.fraud_label,
                total_samples=0,
                results=[]
            )
        
        results = []
        db = SessionLocal()
        fraud_col = get_fraud_column(request.transaction_type)
        
        # Step 3: Process each row
        for row_dict in random_rows:
            # Determine expectation
            val = row_dict.get(fraud_col)
            expected_label = "fraud" if str(val) in ['1', '1.0', 'True'] else "non-fraud"
            
            # Remove label before passing to AI
            model_input = row_dict.copy()
            model_input.pop(fraud_col, None)
            
            # AI Prediction
            detection_result = detect_fraud(model_input, request.transaction_type)
            
            if not detection_result.get("success", False):
                # Log failure but don't crash
                print(f"Detection failed: {detection_result.get('error')}")
                results.append(TestResultItem(
                    fraud_score=0,
                    expected_fraud_label=expected_label,
                    database_id=None,
                    blockchain_tx=None
                ))
                continue
            
            score = detection_result["fraud_score"]
            tx_hash_ref = f"tx_{datetime.now().timestamp()}_{random.randint(1000, 9999)}"
            
            # DB Log
            fraud_log = FraudLog(
                tx_hash=tx_hash_ref,
                transaction_type=request.transaction_type,
                fraud_score=score,
                model_version="v1.0",
                transaction_data=str(model_input)[:500] 
            )
            db.add(fraud_log)
            db.commit()
            
            # Blockchain Log (Log EVERY transaction regardless of score)
            blockchain_tx = None
            print(f"Writing transaction to blockchain (score: {score})...")
            try:
                blockchain_tx = log_fraud_on_chain(
                    score, 
                    "v1.0", 
                    tx_hash_ref
                )
                print(f"✓ Blockchain TX: {blockchain_tx}")
            except Exception as e:
                print(f"✗ Blockchain write failed: {e}")

            results.append(TestResultItem(
                fraud_score=score,
                expected_fraud_label=expected_label,
                database_id=fraud_log.id,
                blockchain_tx=blockchain_tx
            ))
        
        db.close()
        
        return TestResponse(
            transaction_type=request.transaction_type,
            fraud_label=request.fraud_label,
            total_samples=len(results),
            results=results
        )
    
    except Exception as e:
        print(f"Server Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))