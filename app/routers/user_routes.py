from fastapi import APIRouter, Depends, Query
from app.models import User, UserRole
from app.dependencies import get_current_user, require_admin, get_db_session
from app.schemas import UserSchema, UserUpdate, APIResponse, UserPaginatedResponse, UserResponse
from sqlalchemy import or_, func
from datetime import datetime, timezone
from app.security import bcrypt_context
from app.exceptions import UserNotFoundException, AdminCantDeleteHimselfException, AdminCantRevogateHimselfException, UserAlreadyExistsException, EmailAlreadyExistsException, UserRestoreConflictException
from typing import Literal

user_router = APIRouter(prefix="/users", tags=["users"])


@user_router.get("/")
def read_root():
    """Rota raiz da rota de usuario"""
    return {"message": "Bem-vindo ao módulo de usuarios!"}

@user_router.get("/all", response_model=APIResponse[UserPaginatedResponse])
def get_all_users(search: str | None = Query(default = None, description = "Busca por nome de fornecedor, cnpj, email ou telefone"),
                  page: int = Query(default = 1, ge= 1, description = "Numero da pagina"),
                      user_type: Literal["ADMIN", "FUNCIONARIO"] | None = Query(default=None, description="Tipo de usuario"),
                              page_size: int = Query(default = 20, ge = 1 , le = 100, description = "Maximo de itens por pagina"),
                             status_filter: Literal["active", "inactive", "all"] = Query(default="active", description="Filtro de estado: 'active' (padrão), 'inactive' (desativados) ou 'all' (todos)"),
                             db_session=Depends(get_db_session),
                             admin_user=Depends(require_admin )):
    """Retorna todas os usuarios disponíveis no sistema. deletados? sim ou nao"""
    query = db_session.query(User)
    if status_filter== "active":
        query = query.filter(User.deleted_at.is_(None))
    elif status_filter == "inactive":
        query = query.filter(User.deleted_at.is_not(None))
    if search:
        search_term = f"%{search.strip()}%"
        query = query.filter(or_(User.username.ilike(search_term), User.email.ilike(search_term)))
    if user_type is not None:
        query = query.filter(User.role == user_type)
    total = query.count()
    offset = (page - 1) * page_size
    users = query.order_by(User.username.asc()).offset(offset).limit(page_size).all()
    return APIResponse(message="Busca concluida com sucesso", data=UserPaginatedResponse(total=total, page=page, page_size=page_size, items=users))

@user_router.get("/search/{user_id}", response_model=APIResponse[UserResponse])
def get_specific_user(user_id: int, db_session = Depends(get_db_session), admin_user = Depends(require_admin)):
    """Retorna informacao de um usuario especifico"""
    if user_id is not None:
        user = db_session.query(User).filter(User.id == user_id).first()
        if user:
            return APIResponse(message="Informacoes do usuario obtida com sucesso", data=user)
        else:
            raise UserNotFoundException(identifier=str(user_id))
    else:
        raise UserNotFoundException(identifier=str(user_id))

@user_router.patch("/update/{user_id}", response_model=APIResponse[UserResponse])
def modify_user(user_id: int, userUpdate: UserUpdate, db_session = Depends(get_db_session), admin_user = Depends(require_admin)):
    """Modifica um usuario"""
    user = db_session.query(User).filter(User.id == user_id).first()
    if user is None:
        raise UserNotFoundException(identifier=str(user_id))
    if userUpdate.role is not None and userUpdate.role != user.role:
        # Se o admin está editando a si mesmo e tentando remover seu próprio papel de admin
        if user.id == admin_user.id and userUpdate.role != UserRole.ADMIN:
            raise AdminCantRevogateHimselfException()


    conflict_conditions = []

    if (userUpdate.username is not None and userUpdate.username != user.username):
        conflict_conditions.append(User.username == userUpdate.username)
    if (userUpdate.email is not None and userUpdate.email != user.email):
        conflict_conditions.append(User.email == userUpdate.email)

    if conflict_conditions:
        conflict_user = db_session.query(User).filter(User.id != user.id, User.deleted_at.is_(None),or_(*conflict_conditions),).first()
        if conflict_user:
            if conflict_user.username == userUpdate.username:
                raise UserAlreadyExistsException(username=conflict_user.username)
            if conflict_user.email == userUpdate.email:
                raise EmailAlreadyExistsException(email=conflict_user.email)

    update_dict = userUpdate.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(user, field, value)

    user.updated_by = admin_user.id

    db_session.commit()
    db_session.refresh(user)
    return APIResponse(message="Usuario atualizado com sucesso", data=user)


@user_router.delete("/delete/{user_id}", response_model=APIResponse[UserResponse])
def delete_user(user_id : int, db_session = Depends(get_db_session), admin_user = Depends(require_admin)):
    """Desativa um usuario, um usuario nao pode  se desativar"""
    if user_id == admin_user.id:
        raise AdminCantDeleteHimselfException
    user = db_session.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()
    if user is None:
         raise UserNotFoundException(identifier= str(user_id))

    user.deleted_by = admin_user.id
    user.deleted_at = datetime.now(timezone.utc)
    db_session.commit()
    db_session.refresh(user)
    return APIResponse(message="Usuario deletado com sucesso", data=user)

@user_router.patch("/{user_id}/password", response_model=APIResponse[None])
def change_user_password(user_id : int, new_password : str, db_session = Depends(get_db_session), admin_user = Depends(require_admin)):
    """Muda senha de um usuario"""
    user = db_session.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()
    if user is None:
        raise UserNotFoundException(identifier= str(user_id))
    user.password = bcrypt_context.hash(new_password)
    user.updated_by = admin_user.id

    db_session.commit()
    return APIResponse(message="Alteracao de senha feita com sucesso", data=None)

@user_router.patch("/restore/{user_id}", response_model = APIResponse[UserResponse])
def restore_user(user_id, db_session= Depends(get_db_session), admin_user = Depends(require_admin)):
    """Restaura um usuario"""
    user = db_session.query(User).filter(User.id == user_id, User.deleted_at.is_not(None)).first()
    if not user:
        raise UserNotFoundException(identifier=user_id)

    conflicts = (db_session.query(User).filter(User.id != user_id, or_(User.email == user.email,func.lower(User.username) == user.username.strip().lower(),),).all())
    if conflicts:
        details = [f"ID {c.id} ({c.username})" for c in conflicts]
        raise UserRestoreConflictException(conflicting_users=details)

    user.deleted_at = None
    user.deleted_by = None
    user.updated_by = admin_user.id

    db_session.commit()
    db_session.refresh(user)

    return APIResponse(message="Usuario ativado com sucesso", data = user)
