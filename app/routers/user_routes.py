from fastapi import APIRouter, Depends, Query, HTTPException, status
from app.models import User, UserRole
from app.dependencies import get_current_user, require_admin, get_db_session
from app.schemas import UserSchema, UserUpdate, APIResponse
from sqlalchemy import or_
from datetime import datetime, timezone
from app.security import bcrypt_context
from app.exceptions import UserNotFoundException, AdminCantDeleteHimselfException, AdminCantRevogateHimselfException, UserAlreadyExistsException, EmailAlreadyExistsException

user_router = APIRouter(prefix="/users", tags=["users"])


@user_router.get("/")
def read_root():
    """Rota raiz da rota de usuario"""
    return {"message": "Bem-vindo ao módulo de usuarios!"}
#preciso arruamr esse get all
@user_router.get("/all")
def get_all_users(skip:int=0, limit:int = 100, include_deleted: bool = Query(False, description="Se verdadeiro, inclui usuários inativados/excluídos via soft delete"), db_session=Depends(get_db_session), admin_user=Depends(require_admin )):
    """Retorna todas os usuarios disponíveis no sistema. deletados? sim ou nao"""
    if include_deleted is False:
        users = (db_session.query(User).filter(User.deleted_at.is_(None)).offset(skip).limit(limit).all())
    else:
        users = (db_session.query(User).offset(skip).limit(limit).all())
    return users

@user_router.get("/search/{user_id}", response_model=APIResponse[UserSchema])
def get_specific_user(user_id: int, db_session = Depends(get_db_session), admin_user = Depends(require_admin)):
    """Retorna informacao de um usuario especifico"""
    if user_id is not None:
        user = db_session.query(User).filter(User.id == user_id).first()
        if user:
            return user
        else:
            raise UserNotFoundException(identifier=str(user_id))
    else:
        raise UserNotFoundException(identifier=str(user_id))

@user_router.patch("/update/{user_id}", response_model=APIResponse[UserSchema])
def modify_user(user_id: int, userUpdate: UserUpdate, db_session = Depends(get_db_session), admin_user = Depends(require_admin)):
    """Modifica um usuario"""
    user = db_session.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()
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


@user_router.delete("/delete/{user_id}", response_model=APIResponse[UserSchema])
def delete_user(user_id : int, db_session = Depends(get_db_session), admin_user = Depends(require_admin)):
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
    user = db_session.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()
    if user is None:
        raise UserNotFoundException(identifier= str(user_id))
    user.password = bcrypt_context.hash(new_password)
    user.updated_by = admin_user.id

    db_session.commit()
    return APIResponse(message="Alteracao de senha feita com sucesso", data=None)
