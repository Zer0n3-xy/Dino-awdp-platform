from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.database import get_db
from app.models import User

bearer_scheme = HTTPBearer(auto_error=True)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    token = credentials.credentials
    try:
        username = decode_access_token(token)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.scalar(select(User).where(User.username == username))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user
