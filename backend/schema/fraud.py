from pydantic import BaseModel
from typing import List, Dict, Optional


# ============= Input Schemas =============


class HTMLFormInput(BaseModel):
    """Input schema for HTML form submissions."""
    transaction_type: str  # "vehicle", "bank", "ecommerce", or "ethereum"
    form_data: Dict  # Raw form data as key-value pairs


# ============= Output Schemas =============

class ModelScoreDetail(BaseModel):
    """Detail of individual model score."""
    model: str
    fraud_score: int


class FraudDetectionResponse(BaseModel):
    """Response from fraud detection endpoint."""
    success: bool
    fraud_score: int
    transaction_type: str
    model_details: List[Dict]
    database_id: Optional[int] = None


class TxIndex(BaseModel):
    """Transaction record index."""
    tx_hash: str
    transaction_type: str
    model_version: str

