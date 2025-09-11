from jose import jwt, JWTError, ExpiredSignatureError
from datetime import datetime, timedelta
import os

JWT_SECRET_KEY = "M9YLhDx3M1qIGDME0WKkefEMGXf7I7qGUNtQfwUPDroaHIqivf3MSELSOXwERAVK8Q7ojdcn6p73Vrus17IUgqiW436iurKrWiOm9HjtcpxXYQzXqnrqGzCsbKbFPwi7zdGokiyFsDkVMoH71J6T3PE6y3onLjxULNMkDVD6785xMV8b8sZ8MaLp0YhIvfQSjZKyn2pBsb0f84yAn5KUVBgeKu8Hz985l4WxWuoumbP8KIlkYV9EKvzCHdQOSm1g"  # Thay bằng bí mật thực tế
JWT_ALGORITHM = "HS256" 
ACCESS_TOKEN_EXPIRE_DAYS = 7

def create_access_token(user_id: str, wallet_address: str) -> str:
    expires = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    payload = {
        "user_id": user_id,
        "wallet_address": wallet_address,
        "exp": expires,
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def decode_access_token(token: str):
    try:
        return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except ExpiredSignatureError:
        return None
    except JWTError:
        return None
