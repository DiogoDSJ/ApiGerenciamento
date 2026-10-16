from app.models import User, db
from sqlalchemy.orm import sessionmaker, Session
from app.main import algorithm, secret_key
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_db_session():
    try:
        Session = sessionmaker(bind=db)
        session = Session()
        yield session
    finally:
        session.close()

def get_current_user(token: str = Depends(oauth2_scheme), get_db = Depends(get_db_session)):
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais invalidas ou tokmen excpirado", headers={"WWW-Authenticate": "Bearer"})

    try:
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
        get_user_identifier: str = payload.get("sub")
        if get_user_identifier is None:
            raise credentials_exception

    except JWTError:
        # token expirado
        raise credentials_exception

    user = get_db.query(User).filter(User.username == get_user_identifier).first()

    if user is None:
        raise credentials_exception

    return user

def verify_refresh_token(token: str):
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token inválido ou expirado.", headers={"WWW-Authenticate": "Bearer"})

    try:
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])

        token_type = payload.get("type")
        if token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Tipo de token inválido. Esperava-se um refresh token.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        get_user_identifier: str = payload.get("sub")
        if get_user_identifier is None:
            raise credentials_exception

        return get_user_identifier

    except JWTError:
        # token expirado
        raise credentials_exception

def require_admin(current_user: User = Depends(get_current_user)):
    """Trava a rota se o usuário não for administrador."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operação permitida apenas para administradores"
        )
    return current_user
