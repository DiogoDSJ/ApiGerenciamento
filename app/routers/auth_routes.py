from fastapi import APIRouter, Depends, HTTPException, status
from app.models import User
from app.dependencies import get_db_session, get_current_user, verify_refresh_token
from app.security import bcrypt_context, algorithm, token_expire_minutes, secret_key, refresh_token_expire_minutes
from app.schemas import UserSchema, LoginSchema, RefreshTokenRequest, APIResponse, RefreshTokenResponse, TokenSchema
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
from app.exceptions import AuthenticationException, UserAlreadyExistsException, UserNotFoundException, EmailAlreadyExistsException
from sqlalchemy import or_

auth_router = APIRouter(prefix="/auth", tags=["auth"])

@auth_router.get("/")
def read_root():
    """Rota raiz do módulo de autenticação."""
    return {"message": "Bem-vindo ao módulo de autenticação!"}

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

@auth_router.post("/create_user", response_model = APIResponse[UserSchema], status_code=status.HTTP_201_CREATED)
def create_user(user_data: UserSchema, db_session=Depends(get_db_session)):
    """Cria um novo usuário no sistema."""
    user = db_session.query(User).filter(or_(User.username == user_data.username, User.email == user_data.email), User.deleted_at.is_(None)).first()
    if user:
        if user_data.username == user.username:
            raise UserAlreadyExistsException(username=user_data.username)
        elif user_data.email == user.email:
            raise EmailAlreadyExistsException(email=user_data.email)
    else:
        encrypted_password = bcrypt_context.hash(user_data.password)
        new_user = User(username=user_data.username, password=encrypted_password, email=user_data.email, role=user_data.role)
        db_session.add(new_user)
        db_session.commit()
    return APIResponse(message="Usuario criado com sucesso", data=new_user)

@auth_router.post("/login", response_model = APIResponse[TokenSchema], status_code=status.HTTP_200_OK)
def login(loginSchema: LoginSchema = Depends(), db_session=Depends(get_db_session)):
    """Autentica um usuário no sistema."""
    user = authenticate_user(loginSchema.username, loginSchema.password, db_session)
    token = create_acess_token(user.username)
    refresh_token = create_refresh_token(user.username)  # Cria um token de atualização (refresh token)
    return APIResponse(message="Login realizado com sucesso", data=TokenSchema(access_token = token, refresh_token = refresh_token))

@auth_router.get("/me", response_model = APIResponse[UserSchema], status_code=status.HTTP_200_OK)
def read_current_user(current_user: User = Depends(get_current_user)):
    return APIResponse(message="Usuario está autenticado", data = current_user)

@auth_router.post("/refresh", response_model = APIResponse[RefreshTokenResponse], status_code=status.HTTP_200_OK)
def refresh_token_endpoint(payload_data: RefreshTokenRequest, db_session = Depends(get_db_session)): # nao coloquei uma forma de inutilizar o refresh token antigo
    """Recarrega o acess token e da um novo refresh token"""
    username = verify_refresh_token(payload_data.refresh_token)
    user = db_session.query(User).filter(User.username == username, User.deleted_at.is_(None)).first()

    if not user:
        raise UserNotFoundException(username)

    new_acess_token = create_acess_token(user.username)

    return APIResponse(
        message="Token de acesso renovado.",
        data = RefreshTokenResponse(acess_token=new_acess_token),
    )


