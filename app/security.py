import os
from dotenv import load_dotenv
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
from app.exceptions import AuthenticationException
from app.models import User

load_dotenv()
secret_key = os.getenv("SECRET_KEY")
algorithm = os.getenv("ALGORITHM")
token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 1))
refresh_token_expire_minutes = int(os.getenv("REFRESH_TOKEN_EXPIRE_MINUTES", 1))


bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_acess_token(username):
    """Função para criar um token de autenticação (JWT) para o usuário."""
    expire_data = datetime.now(timezone.utc) + timedelta(minutes=token_expire_minutes)
    payload = {"sub": username, "exp": expire_data, "iat": datetime.now(timezone.utc), "type": "access"}
    encoded_jwt = jwt.encode(payload, secret_key, algorithm=algorithm)
    return encoded_jwt

def create_refresh_token(username):
    """Função para criar um token de atualização (refresh token) para o usuário."""
    expire_data = datetime.now(timezone.utc) + timedelta(minutes=refresh_token_expire_minutes)
    payload = {"sub": username, "exp": expire_data, "iat": datetime.now(timezone.utc), "type": "refresh"}
    encoded_jwt = jwt.encode(payload, secret_key, algorithm=algorithm)
    return encoded_jwt

def authenticate_user(username, password, db_session):
    """Função para autenticar um usuário com base no nome de usuário e senha."""
    user = db_session.query(User).filter(User.username == username, User.deleted_at.is_(None)).first()
    if not user or not bcrypt_context.verify(password, user.password):
        raise AuthenticationException()
    return user
