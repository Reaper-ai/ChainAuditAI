import json
import hashlib
import os
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

# Web3 setup
w3 = Web3(Web3.HTTPProvider(os.getenv("RPC_URL")))

account = w3.eth.account.from_key(os.getenv("PRIVATE_KEY"))

with open("blockchain/abi.json") as f:
    abi = json.load(f)

contract = w3.eth.contract(
    address=Web3.to_checksum_address(os.getenv("CONTRACT_ADDRESS")),
    abi=abi
)


# print("Python wallet address:", account.address)
# print("Balance (ETH):", w3.eth.get_balance(account.address))


def log_fraud_to_chain(transaction_data, fraud_score):
    tx_hash = hashlib.sha256(str(transaction_data).encode()).hexdigest()

    txn = contract.functions.logFraud(
        Web3.to_bytes(hexstr=tx_hash),
        int(fraud_score),
        "v1.0"
    ).build_transaction({
        "from": account.address,
        "nonce": w3.eth.get_transaction_count(account.address),
        "gas": 200000,
        "gasPrice": w3.to_wei("10", "gwei")
    })

    signed_txn = account.sign_transaction(txn)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)

    print("✅ Logged on Ethereum")
    print("Tx Hash:", tx_hash.hex())
