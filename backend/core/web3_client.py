from web3 import Web3
import json
from core.config import RPC_URL, CONTRACT_ADDRESS, ABI_PATH

w3 = Web3(Web3.HTTPProvider(RPC_URL))

with open(ABI_PATH) as f:
    abi = json.load(f)

contract = w3.eth.contract(
    address=Web3.to_checksum_address(CONTRACT_ADDRESS),
    abi=abi
)
