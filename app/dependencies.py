from app.models import User, db
from sqlalchemy.orm import sessionmaker, Session
from app.security import algorithm, secret_key
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt
from app.exceptions import InvalidCredentialsException, InvalidTokenType, InsufficientPermision


auth_scheme = HTTPBearer()

def get_db_session():
    try:
        Session = sessionmaker(bind=db)
        session = Session()
        yield session
    finally:
        session.close()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(auth_scheme), get_db = Depends(get_db_session)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
        get_user_identifier: str = payload.get("sub")
        if get_user_identifier is None:
            raise InvalidCredentialsException()

    except JWTError:
        # token expirado
        raise InvalidCredentialsException()

    user = get_db.query(User).filter(User.username == get_user_identifier).first()

    if user is None:
        raise InvalidCredentialsException()

    return user

def verify_refresh_token(token: str):
    try:
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])

        token_type = payload.get("type")
        if token_type != "refresh":
            raise InvalidTokenType()
        get_user_identifier: str = payload.get("sub")
        if get_user_identifier is None:
            raise InvalidCredentialsException()

        return get_user_identifier

    except JWTError:
        # token expirado
        raise InvalidCredentialsException()

def require_admin(current_user: User = Depends(get_current_user)):
    """Trava a rota se o usuário não for administrador."""
    if current_user.role != "admin":
        raise InsufficientPermision()
    return current_user
