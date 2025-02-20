from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from ..core.security import verify_password
from ..config.settings import settings
from ..services.user_service import UserService
from ..db.repositories.user import UserRepository
from ..db.database import Database

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/login")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """验证当前用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    db = Database.get_db()
    user_repo = UserRepository(db)
    user_service = UserService(user_repo)
    user = await user_service.get_user(user_id)
    if user is None:
        raise credentials_exception
    return user 