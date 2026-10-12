from fastapi import APIRouter, Depends, HTTPException, status
from app.models import User
from app.dependencies import get_db_session
from app.main import bcrypt_context, algorithm, token_expire_minutes, secret_key, refresh_token_expire_minutes
from app.schemas import UserSchema, LoginSchema
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone

auth_router = APIRouter(prefix="/auth", tags=["auth"])

@auth_router.get("/")
async def read_root():
    """Rota raiz do módulo de autenticação."""
    return {"message": "Bem-vindo ao módulo de autenticação!"}

def create_token(username):
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
    user = db_session.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")
    if not bcrypt_context.verify(password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Senha incorreta.")
    return user

@auth_router.post("/create_user")
async def create_user(user_data: UserSchema, db_session=Depends(get_db_session)):
    """Cria um novo usuário no sistema."""
    user = db_session.query(User).filter((User.username == user_data.username) | (User.email == user_data.email)).first()
    if user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Usuário já existe.")
    else:
        encrypted_password = bcrypt_context.hash(user_data.password)
        new_user = User(username=user_data.username, password=encrypted_password, email=user_data.email, role=user_data.role)
        db_session.add(new_user)
        db_session.commit()
        raise HTTPException(status_code=status.HTTP_201_CREATED, detail=f"Usuário criado com sucesso. {user_data.email} {user_data.username} {user_data.role}")

@auth_router.post("/login")
async def login(loginSchema: LoginSchema, db_session=Depends(get_db_session)):
    """Autentica um usuário no sistema."""
    user = authenticate_user(loginSchema.username, loginSchema.password, db_session)
    token = create_token(user.username)
    refresh_token = create_refresh_token(user.username)  # Cria um token de atualização (refresh token)
    raise HTTPException(status_code=status.HTTP_200_OK, detail=f"Login bem-sucedido.", headers={"Authorization": f"Bearer {token}", "Refresh-Token": f"Bearer {refresh_token}"})
