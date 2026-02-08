from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from datetime import datetime
from core.database import Base


class FraudLog(Base):
    """
    Fraud detection log stored in database.
    
    Records fraud detection results for all transactions,
    referenced by blockchain transaction hash.
    """
    __tablename__ = "fraud_logs"

    id = Column(Integer, primary_key=True, index=True)
    
    # Transaction identification
    tx_hash = Column(String, unique=True, index=True)
    transaction_type = Column(String, index=True)  # vehicle, bank, ecommerce, ethereum
    
    # Fraud detection results
    fraud_score = Column(Integer)  # 0-100
    # Model information
    model_version = Column(String)
    
    # Raw transaction data (for future audits/analysis)
    transaction_data = Column(JSON, nullable=True)
    
    # Blockchain info
    blockchain_timestamp = Column(Integer, nullable=True)
    gas_used = Column(Integer, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<FraudLog(id={self.id}, tx_hash={self.tx_hash}, fraud_score={self.fraud_score})>"

