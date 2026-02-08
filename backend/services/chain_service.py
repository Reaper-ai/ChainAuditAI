from core.web3_client import w3, contract

def get_onchain_fraud_data(tx_hash: str):
    receipt = w3.eth.get_transaction_receipt(tx_hash)
    block = w3.eth.get_block(receipt.blockNumber)

    events = contract.events.FraudLogged().process_receipt(receipt)
    event = events[0]["args"]

    return {
        "fraud_score": event["fraudScore"],
        "model_version": event["modelVersion"],
        "timestamp": block.timestamp,
        "gas_used": receipt.gasUsed
    }

import json
from web3 import Web3
from core.web3_client import w3, contract
# Make sure ACCOUNT_ADDRESS and PRIVATE_KEY are in your core/config.py
from core.config import CONTRACT_ADDRESS, PRIVATE_KEY 

def get_onchain_fraud_data(tx_hash: str):
    """Read fraud data from blockchain (Existing function)."""
    try:
        receipt = w3.eth.get_transaction_receipt(tx_hash)
        block = w3.eth.get_block(receipt.blockNumber)
        events = contract.events.FraudLogged().process_receipt(receipt)
        if not events: return None
        event = events[0]["args"]
        return {
            "fraud_score": event["fraudScore"],
            "model_version": event["modelVersion"],
            "timestamp": block.timestamp,
            "gas_used": receipt.gasUsed,
            "tx_hash": tx_hash
        }
    except Exception as e:
        print(f"Error fetching chain data: {e}")
        return None

def log_fraud_on_chain(fraud_score: int, model_version: str, reference_id: str):
    """
    Write fraud record to blockchain.
    """
    if not contract:
        print("Error: Contract not initialized.")
        return None

    try:
        print(f"Mining transaction for Ref ID: {reference_id}...")
        
        # 1. Build Transaction
        tx = contract.functions.logFraud(
            int(fraud_score),
            str(model_version),
            str(reference_id)
        ).build_transaction({
            'from': CONTRACT_ADDRESS,
            'nonce': w3.eth.get_transaction_count(CONTRACT_ADDRESS),
            'gas': 2000000,
            'gasPrice': w3.to_wei('20', 'gwei')
        })

        # 2. Sign Transaction
        signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)

        # 3. Send Transaction
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        
        # 4. Wait for Receipt (Blocking call to ensure it's mined before returning)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"Transaction mined: {receipt.transactionHash.hex()}")
        
        return receipt.transactionHash.hex()

    except Exception as e:
        print(f"Blockchain Write Error: {e}")
        return None