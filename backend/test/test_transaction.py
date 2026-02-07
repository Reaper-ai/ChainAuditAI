import joblib
import numpy as np
from backend.tochain import log_fraud_to_chain


transaction = np.array([100.0, 1.0, 0.0, 0.0, 1.0])  # Example transaction features
# Fraud score (simple normalization)
raw_score = 0.5
fraud_score = int((1 - raw_score) * 50)
fraud_score = max(0, min(100, fraud_score))

print("Fraud Score:", fraud_score)

# Send to Ethereum
log_fraud_to_chain(transaction.tolist(), fraud_score)
