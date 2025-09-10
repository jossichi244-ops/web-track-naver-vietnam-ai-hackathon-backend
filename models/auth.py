from pydantic import BaseModel

class ChallengeRequest(BaseModel):
    wallet_address: str

class ChallengeResponse(BaseModel):
    wallet_address: str
    challenge: str
    expires_at: str

class VerifyRequest(BaseModel):
    wallet_address: str
    signature: str

class VerifyResponse(BaseModel):
    user_id: str
    wallet_address: str
    access_token: str
