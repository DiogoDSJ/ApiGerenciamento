from fastapi import APIRouter, Depends
from app.models import User
from app.dependencies import get_db_session, get_current_user, verify_refresh_token
from app.security import bcrypt_context, create_acess_token, create_refresh_token, authenticate_user, algorithm, token_expire_minutes, secret_key, refresh_token_expire_minutes
from app.schemas import UserSchema, LoginSchema, RefreshTokenRequest, APIResponse, RefreshTokenResponse, TokenSchema
from app.exceptions import UserAlreadyExistsException, UserNotFoundException, EmailAlreadyExistsException
from sqlalchemy import or_


auth_router = APIRouter(prefix="/auth", tags=["auth"])

@auth_router.get("/")
def read_root():
    """Rota raiz do módulo de autenticação."""
    return {"message": "Bem-vindo ao módulo de autenticação!"}



@auth_router.post("/create_user", response_model = APIResponse[UserSchema])
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

@auth_router.post("/login", response_model = APIResponse[TokenSchema])
def login(loginSchema: LoginSchema = Depends(), db_session=Depends(get_db_session)):
    """Autentica um usuário no sistema."""
    user = authenticate_user(loginSchema.username, loginSchema.password, db_session)
    token = create_acess_token(user.username)
    refresh_token = create_refresh_token(user.username)  # Cria um token de atualização (refresh token)
    return APIResponse(message="Login realizado com sucesso", data=TokenSchema(access_token = token, refresh_token = refresh_token))

@auth_router.get("/me", response_model = APIResponse[UserSchema])
def read_current_user(current_user: User = Depends(get_current_user)):
    """Le o usuario logado e devolve o objeto para ver se esta autenticado"""
    return APIResponse(message="Usuario está autenticado", data = current_user)

@auth_router.post("/refresh", response_model = APIResponse[RefreshTokenResponse])
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


