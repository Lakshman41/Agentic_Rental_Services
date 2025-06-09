# File: agentic_rental_platform/app/core/security.py
from datetime import datetime, timedelta, timezone
from typing import Optional, Any, Union

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings 
from app.core.logging import logger   

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS
JWT_SECRET_KEY = settings.JWT_SECRET_KEY # This is now guaranteed by validator in config.py
JWT_REFRESH_SECRET_KEY = settings.JWT_REFRESH_SECRET_KEY # This is now guaranteed by validator in config.py


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Error verifying password: {e}")
        return False

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"exp": expire, "sub": str(subject), "type": "access"}
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}
    encoded_jwt = jwt.encode(to_encode, JWT_REFRESH_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str, secret_key: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, secret_key, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        logger.warning(f"JWT Error decoding token: {e} (token: {token[:10]}...)")
        return None
    except Exception as e:
        logger.error(f"Unexpected error decoding token: {e}")
        return None

if __name__ == "__main__":
    import time
    logger.info("Running security.py self-test (via python -m)...")
    
    password = "mypassword123"
    hashed_pw = get_password_hash(password)
    logger.info(f"Original: {password}, Hashed: {hashed_pw}")
    assert verify_password(password, hashed_pw)
    assert not verify_password("wrongpassword", hashed_pw)
    logger.info("Password hashing verified.")

    user_id_test = "user_via_m_test_002"
    access_token = create_access_token(subject=user_id_test)
    refresh_token = create_refresh_token(subject=user_id_test)
    logger.info(f"Access Token: {access_token}")
    logger.info(f"Refresh Token: {refresh_token}")

    decoded_access = decode_token(access_token, JWT_SECRET_KEY)
    decoded_refresh = decode_token(refresh_token, JWT_REFRESH_SECRET_KEY)
    
    assert decoded_access and decoded_access["sub"] == user_id_test and decoded_access["type"] == "access"
    assert decoded_refresh and decoded_refresh["sub"] == user_id_test and decoded_refresh["type"] == "refresh"
    logger.info(f"Decoded Access: {decoded_access}")
    logger.info(f"Decoded Refresh: {decoded_refresh}")

    expired_access_token = create_access_token(subject=user_id_test, expires_delta=timedelta(seconds=1))
    time.sleep(1.5) 
    decoded_expired = decode_token(expired_access_token, JWT_SECRET_KEY)
    assert decoded_expired is None 
    logger.info(f"Decoded Expired Access (should be None): {decoded_expired}")
    logger.info("Token functions seem to work.")