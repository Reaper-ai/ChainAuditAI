from fastapi import APIRouter
from core.database import SessionLocal
from models.fraud_log import FraudLog
# Ensure this import matches your file structure
from services.chain_service import get_onchain_fraud_data

# Prefix MUST be 
router = APIRouter(prefix="/stats", tags=["Dashboard"])

@router.get("/")
def get_dashboard_stats():
    """
    Get fraud stats and recent logs.
    """
    try:
        db = SessionLocal()
        # Fetch all records, sorted by newest first
        all_records = db.query(FraudLog).order_by(FraudLog.created_at.desc()).all()
        db.close()

        response_data = []
        
        # Loop through records
        # LIMIT chain lookups to the top 5 to prevent timeouts
        for index, record in enumerate(all_records):
            chain_data = None
            
            # Only check blockchain for the most recent 5 records
            # and only if they have a valid 0x hash
            if index < 5 and record.tx_hash and record.tx_hash.startswith("0x"):
                try:
                    chain_data = get_onchain_fraud_data(record.tx_hash)
                except Exception as e:
                    print(f"Error fetching chain data for {record.tx_hash}: {e}")

            item = {
                "id": record.id,
                "tx_hash": record.tx_hash,
                "transaction_type": record.transaction_type,
                "fraud_score": record.fraud_score,
                "model_version": record.model_version,
                "created_at": record.created_at.isoformat() if record.created_at else None,
                "blockchain_data": chain_data 
            }
            
            response_data.append(item)
        
        return {
            "total_records": len(response_data),
            "records": response_data
        }
        
    except Exception as e:
        print(f"Dashboard Error: {e}")
        return {
            "total_records": 0,
            "records": [],
            "error": str(e)
        }