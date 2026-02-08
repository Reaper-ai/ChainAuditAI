import os

RPC_URL = os.getenv("RPC_URL")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")
CHAIN_ID = 11155111  # Sepolia
PRIVATE_KEY = os.getenv("PRIVATE_KEY")

DATABASE_URL = "sqlite:///./fraud.db"
ABI_PATH = "blockchain/abi.json"
MODEL_PATH = "../model_wts"
