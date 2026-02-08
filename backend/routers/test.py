from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
import pandas as pd
from datetime import datetime
import random
from core.database import SessionLocal
from models.fraud_log import FraudLog
from services.ai_service import detect_fraud, initialize_service

router = APIRouter(prefix="/test", tags=["Testing & Fraud Detection"])

# Initialize service on startup
initialize_service()


# ============= Input Schemas =============

class TestRequest(BaseModel):
    """
    Request to test fraud detection with random subset from test data.
    
    Frontend specifies:
    - transaction_type: Which model to use (vehicle, bank, ecommerce, ethereum)
    - fraud_label: "fraud" or "non-fraud" to select which subset to test
    """
    transaction_type: str  # "vehicle", "bank", "ecommerce", or "ethereum"
    fraud_label: str  # "fraud" or "non-fraud"


# ============= Output Schemas =============

class TestResultItem(BaseModel):
    """Single test result."""
    fraud_score: int
    expected_fraud_label: Optional[str] = None
    database_id: Optional[int] = None
    blockchain_tx: Optional[str] = None


class TestResponse(BaseModel):
    """Response from test endpoint with 5 results."""
    transaction_type: str
    fraud_label: str  # Expected label ("fraud" or "non-fraud")
    total_samples: int  # Should be 5
    results: List[TestResultItem]


# ============= Helper Functions =============

def load_test_data(transaction_type: str) -> pd.DataFrame:
    """
    Load appropriate test data CSV based on transaction type.
    
    Args:
        transaction_type: One of "vehicle", "bank", "ecommerce", "ethereum"
    
    Returns:
        DataFrame with test data
    """
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
        df = pd.read_csv(filepath)
        return df
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


def get_random_subset(df: pd.DataFrame, fraud_label: str, n_samples: int = 5) -> List[Dict]:
    """
    Get random subset of fraud or non-fraud rows.
    
    Args:
        df: DataFrame with test data
        fraud_label: "fraud" or "non-fraud"
        n_samples: Number of random rows to select (default 5)
    
    Returns:
        List of dictionaries (rows) with fraud column included
    """
    fraud_col = get_fraud_column_from_df(df)
    
    if fraud_label == "fraud":
        subset_df = df[df[fraud_col] == 1]
    else:
        subset_df = df[df[fraud_col] == 0]
    
    if len(subset_df) < n_samples:
        selected = subset_df
    else:
        # Use random_state=None for true randomness each time
        selected = subset_df.sample(n=n_samples, random_state=None)
    
    return [row.to_dict() for _, row in selected.iterrows()]


def get_fraud_column_from_df(df: pd.DataFrame) -> str:
    """Detect fraud column from DataFrame."""
    for col in df.columns:
        if 'fraud' in col.lower() or 'fraudulent' in col.lower():
            return col
    raise ValueError("No fraud column found in test data")


# ============= Endpoints =============

@router.post("/run-test", response_model=TestResponse)
def run_fraud_test(request: TestRequest):
    """
    Run fraud detection test on 5 random rows from test data.
    
    Pipeline:
    1. Load test data for transaction_type
    2. Filter by fraud_label (fraud or non-fraud)
    3. Select 5 random rows from the 25 available
    4. Run detect_fraud on each row
    5. Log each result to database
    6. If fraud_score > 50, log to blockchain
    7. Return all 5 results with scores and blockchain status
    
    Args:
        request: TestRequest with transaction_type and fraud_label
    
    Returns:
        TestResponse with 5 detection results
    
    Example:
        POST /test/run-test
        {
            "transaction_type": "vehicle",
            "fraud_label": "fraud"
        }
    """
    valid_types = ["vehicle", "bank", "ecommerce", "ethereum"]
    valid_labels = ["fraud", "non-fraud"]
    
    if request.transaction_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid transaction_type. Must be one of: {', '.join(valid_types)}"
        )
    
    if request.fraud_label not in valid_labels:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid fraud_label. Must be 'fraud' or 'non-fraud'"
        )
    
    try:
        # Step 1: Load test data
        df = load_test_data(request.transaction_type)
        
        # Step 2-3: Get 5 random rows (from 25 available per label)
        random_rows = get_random_subset(df, request.fraud_label, n_samples=5)
        
        if not random_rows:
            raise HTTPException(
                status_code=400,
                detail=f"No {request.fraud_label} samples available"
            )
        
        results = []
        db = SessionLocal()
        fraud_col = get_fraud_column(request.transaction_type)
        
        # Step 4-6: Process each row
        for row_dict in random_rows:
            # Extract expected fraud label before removing it
            expected_fraud = row_dict.get(fraud_col)
            expected_label = "fraud" if expected_fraud == 1 or expected_fraud == 1.0 else "non-fraud"
            
            # Remove fraud column from input data (don't pass to model)
            row_dict.pop(fraud_col, None)
            
            # Step 4: Run detection
            detection_result = detect_fraud(row_dict, request.transaction_type)
            
            if not detection_result.get("success", False):
                error_msg = detection_result.get('error', 'Unknown error')
                print(f"Warning: Detection failed for row: {error_msg}")
                print(f"Row data keys: {list(row_dict.keys())}")
                continue
            
            # Step 5: Log to database
            fraud_log = FraudLog(
                tx_hash=f"test_{datetime.now().timestamp()}_{random.randint(1000, 9999)}",
                transaction_type=request.transaction_type,
                fraud_score=detection_result["fraud_score"],
                model_version="v1",
                transaction_data=row_dict
            )
            db.add(fraud_log)
            db.flush()
            
            blockchain_tx = None
            # Skip blockchain logging - not needed for basic tests
            
            db.commit()
            
            # Collect result
            results.append(TestResultItem(
                fraud_score=detection_result["fraud_score"],
                expected_fraud_label=expected_label,
                database_id=fraud_log.id,
                blockchain_tx=blockchain_tx
            ))
        
        db.close()
        
        # Step 7: Return results
        return TestResponse(
            transaction_type=request.transaction_type,
            fraud_label=request.fraud_label,
            total_samples=len(results),
            results=results
        )
    
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============= Single Transaction Detection =============

class DetectRequest(BaseModel):
    """Detect fraud for a single transaction"""
    transaction_type: str
    tx_hash: Optional[str] = None
    transaction_data: Dict = {}


class DetectResponse(BaseModel):
    """Response for single transaction detection"""
    transaction_type: str
    fraud_score: int
    database_id: int
    blockchain_tx: Optional[str] = None


@router.post("/detect", response_model=DetectResponse)
def detect_transaction(request: DetectRequest):
    """Detect fraud for a single transaction"""
    try:
        db = SessionLocal()
        
        # Detect fraud
        detection_result = detect_fraud(
            request.transaction_type,
            request.transaction_data
        )
        
        # Log to database
        fraud_log = FraudLog(
            transaction_type=request.transaction_type,
            fraud_score=detection_result["fraud_score"],
            tx_hash=request.tx_hash,
            timestamp=datetime.utcnow()
        )
        db.add(fraud_log)
        db.commit()
        db.refresh(fraud_log)
        
        blockchain_tx = None
        # Skip blockchain logging for now - not needed for basic functionality
        
        db.close()
        
        return DetectResponse(
            transaction_type=request.transaction_type,
            fraud_score=detection_result["fraud_score"],
            database_id=fraud_log.id,
            blockchain_tx=blockchain_tx
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

