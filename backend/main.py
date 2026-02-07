from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime
from web3 import Web3
import json
import os

# =========================
# CONFIG
# =========================

RPC_URL = os.getenv("RPC_URL")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")

CHAIN_ID = 11155111  # Sepolia

DATABASE_URL = "sqlite:///./fraud.db"

ABI_PATH = "blockchain/abi.json"

# =========================
# WEB3 SETUP
# =========================

w3 = Web3(Web3.HTTPProvider(RPC_URL))

with open(ABI_PATH) as f:
    abi = json.load(f)

contract = w3.eth.contract(
    address=Web3.to_checksum_address(CONTRACT_ADDRESS),
    abi=abi
)

# =========================
# DATABASE SETUP
# =========================

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class FraudLog(Base):
    __tablename__ = "fraud_logs"

    id = Column(Integer, primary_key=True, index=True)
    tx_hash = Column(String, unique=True, index=True, nullable=False)
    transaction_type = Column(String)
    status = Column(String, default="confirmed")
    created_at = Column(DateTime, default=datetime.now(datetime.timezone.utc))


Base.metadata.create_all(bind=engine)

# =========================
# FASTAPI APP
# =========================

app = FastAPI(
    title="FraudProof Ledger API",
    description="AI + Ethereum fraud audit backend",
    version="1.0"
)

# =========================
# SCHEMAS
# =========================

class LogRequest(BaseModel):
    tx_hash: str
    transaction_type: str


# =========================
# ENDPOINTS
# =========================

@app.post("/log")
def store_transaction(log: LogRequest):
    db = SessionLocal()

    existing = db.query(FraudLog).filter_by(tx_hash=log.tx_hash).first()
    if existing:
        raise HTTPException(status_code=400, detail="Transaction already exists")

    record = FraudLog(
        tx_hash=log.tx_hash,
        transaction_type=log.transaction_type,
        status="confirmed")

    db.add(record)
    db.commit()
    db.refresh(record)

    return {
        "message": "Transaction indexed successfully",
        "tx_hash": log.tx_hash
    }


@app.get("/transactions")
def list_transactions():
    db = SessionLocal()
    records = db.query(FraudLog).order_by(FraudLog.created_at.desc()).all()

    return [
        {
            "tx_hash": r.tx_hash,
            "transaction_type": r.transaction_type,
            "model_version": r.model_version,
            "created_at": r.created_at,
            "status": r.status
        }
        for r in records
    ]


@app.get("/transaction/{tx_hash}")
def get_transaction_details(tx_hash: str):
    # 1. Get transaction receipt
    try:
        receipt = w3.eth.get_transaction_receipt(tx_hash)
    except:
        raise HTTPException(status_code=404, detail="Transaction not found on chain")

    # 2. Get block timestamp
    block = w3.eth.get_block(receipt.blockNumber)
    timestamp = block.timestamp

    # 3. Decode FraudLogged event
    events = contract.events.FraudLogged().process_receipt(receipt)

    if not events:
        raise HTTPException(status_code=400, detail="No fraud event found")

    event = events[0]["args"]

    return {
        "tx_hash": tx_hash,
        "block_number": receipt.blockNumber,
        "timestamp": timestamp,
        "fraud_score": event["fraudScore"],
        "model_version": event["modelVersion"],
        "transaction_hash_proof": event["transactionHash"].hex(),
        "gas_used": receipt.gasUsed
    }
