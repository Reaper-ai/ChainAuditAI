from pydantic import BaseModel
from typing import List

class ManualTestInput(BaseModel):
    features: List[float]

class BulkTestInput(BaseModel):
    records: List[List[float]]

class TxIndex(BaseModel):
    tx_hash: str
    transaction_type: str
    model_version: str
