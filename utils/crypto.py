from eth_account import Account
from eth_account.messages import encode_defunct

def verify_signature(wallet_address: str, challenge: str, signature: str) -> bool:
    """
    Verify signature from MetaMask
    """
    try:
        message = encode_defunct(text=challenge)
        recovered_address = Account.recover_message(message, signature=signature)
        return recovered_address.lower() == wallet_address.lower()
    except Exception as e:
        print("Verify error:", e)
        return False
