from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from core.database import Base

class FraudLog(Base):
    __tablename__ = "fraud_logs"

    id = Column(Integer, primary_key=True)
    tx_hash = Column(String, unique=True, index=True)
    transaction_type = Column(String)
    model_version = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
