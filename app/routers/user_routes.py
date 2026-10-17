from fastapi import APIRouter, Depends, Query, HTTPException, status
from app.models import User, UserRole
from app.dependencies import get_current_user, require_admin, get_db_session
from app.schemas import UserSchema, UserUpdate
from sqlalchemy import or_
from datetime import datetime, timezone
from app.security import bcrypt_context

user_router = APIRouter(prefix="/users", tags=["users"])


@user_router.get("/")
async def read_root():
    """Rota raiz da rota de usuario"""
    return {"message": "Bem-vindo ao módulo de usuarios!"}

@user_router.get("/all")
def get_all_users(skip:int=0, limit:int = 100, include_deleted: bool = Query(False, description="Se verdadeiro, inclui usuários inativados/excluídos via soft delete"), db_session=Depends(get_db_session), admin_user=Depends(require_admin )):
    """Retorna todas os usuarios disponíveis no sistema. deletados? sim ou nao"""
    if include_deleted is False:
        users = (db_session.query(User).filter(User.deleted_at.is_(None)).offset(skip).limit(limit).all())
    else:
        users = (db_session.query(User).offset(skip).limit(limit).all())
    return users

@user_router.get("/search/{user_id}")
def get_specific_user(user_id: int, db_session = Depends(get_db_session), admin_user = Depends(require_admin)):
    """Retorna informacao de um usuario especifico"""
    if user_id is not None:
        user = db_session.query(User).filter(User.id == user_id).first()
        if user:
            return user
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario não encontrado.")
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario não encontrado.")

@user_router.patch("/modify/{user_id}")
def modify_user(user_id: int, userUpdate: UserUpdate, db_session = Depends(get_db_session), admin_user = Depends(require_admin)):
    """Modifica um usuario"""
    user = db_session.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario não encontrado.")
    if userUpdate.role is not None and userUpdate.role != user.role:
        # Se o admin está editando a si mesmo e tentando remover seu próprio papel de admin
        if user.id == admin_user.id and userUpdate.role != UserRole.ADMIN:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Você não pode revogar seus próprios privilégios de administrador.",)


    conflict_conditions = []

    if (userUpdate.username is not None and userUpdate.username != user.username):
        conflict_conditions.append(User.username == userUpdate.username)
    if (userUpdate.email is not None and userUpdate.email != user.email):
        conflict_conditions.append(User.email == userUpdate.email)

    if conflict_conditions:
        conflict_user = db_session.query(User).filter(User.id != user.id, User.deleted_at.is_(None),or_(*conflict_conditions),).first()

    if conflict_user:
        if conflict_user.username == userUpdate.username:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Nome de usuario ja em uso")
        if conflict_user.email == userUpdate.email:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email ja em uso")

    update_dict = userUpdate.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(user, field, value)

    user.updated_by = admin_user.id

    db_session.commit()
    db_session.refresh(user)
    return user


@user_router.delete("/delete/{user_id}")
def delete_user(user_id : int, db_session = Depends(get_db_session), admin_user = Depends(require_admin)):
    if user_id == admin_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Você não pode excluir sua própria conta de administrador.",
        )
    user = db_session.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario não encontrado.")

    user.deleted_by = admin_user.id
    user.deleted_at = datetime.now(timezone.utc)
    db_session.commit()
    db_session.refresh(user)
    return user

@user_router.patch("/{user_id}/password")
def change_user_password(user_id : int, new_password : str, db_session = Depends(get_db_session), admin_user = Depends(require_admin)):
    user = db_session.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario não encontrado.")
    user.password = bcrypt_context.hash(new_password)
    user.updated_by = admin_user.id

    db_session.commit()
    return None
