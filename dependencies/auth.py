from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError, ExpiredSignatureError

JWT_SECRET_KEY = "M9YLhDx3M1qIGDME0WKkefEMGXf7I7qGUNtQfwUPDroaHIqivf3MSELSOXwERAVK8Q7ojdcn6p73Vrus17IUgqiW436iurKrWiOm9HjtcpxXYQzXqnrqGzCsbKbFPwi7zdGokiyFsDkVMoH71J6T3PE6y3onLjxULNMkDVD6785xMV8b8sZ8MaLp0YhIvfQSjZKyn2pBsb0f84yAn5KUVBgeKu8Hz985l4WxWuoumbP8KIlkYV9EKvzCHdQOSm1g"  # Thay bằng bí mật thực tế
JWT_ALGORITHM = "HS256"     

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    token = credentials.credentials
    try:
        # Giải mã JWT
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")
        wallet_address = payload.get("wallet_address")

        if not user_id or not wallet_address:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )

        return {
            "user_id": user_id,
            "wallet_address": wallet_address,
        }

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
