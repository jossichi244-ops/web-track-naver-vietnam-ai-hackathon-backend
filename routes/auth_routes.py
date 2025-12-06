from fastapi import APIRouter
from models.auth import ChallengeRequest, ChallengeResponse, VerifyRequest, VerifyResponse
from controllers import auth_controller

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/challenge", response_model=ChallengeResponse)
async def create_challenge(req: ChallengeRequest):
    challenge, expires_at = await auth_controller.create_challenge(req.wallet_address)
    return ChallengeResponse(
        wallet_address=req.wallet_address,
        challenge=challenge,
        expires_at=expires_at
    )


@router.post("/verify", response_model=VerifyResponse)
async def verify_user(req: VerifyRequest):
    user, access_token = await auth_controller.verify_user(req.wallet_address, req.signature)
    return VerifyResponse(
        user_id=user["_id"],
        wallet_address=req.wallet_address,
        access_token=access_token
    )
