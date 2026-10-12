from fastapi import APIRouter, Depends, HTTPException, status
from app.models import Category
from app.dependencies import get_db_session, get_current_user, require_admin
from app.schemas import CategorySchema
from datetime import datetime, timezone

category_router = APIRouter(prefix="/category", tags=["category"])

@category_router.get("/list")
async def return_all_category(skip:int=0, limit:int = 100, db_session=Depends(get_db_session), current_user=Depends(get_current_user)):
    """Retorna todas as categorias disponíveis no sistema."""
    categories = (db_session.query(Category).filter(Category.deleted_at.is_(None)).offset(skip).limit(limit).all())
    return categories

@category_router.post("/create")
async def create_category(category_data: CategorySchema, db_session=Depends(get_db_session), current_user=Depends(get_current_user)):
    """Cria uma nova categoria no sistema."""
    category = db_session.query(Category).filter(Category.name == category_data.name, Category.deleted_at.is_(None)).first()
    if category:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Categoria já existe.")
    new_category = Category(name=category_data.name, created_by=current_user.id)
    db_session.add(new_category)
    db_session.commit()
    raise HTTPException(status_code=status.HTTP_201_CREATED, detail=f"Categoria criada com sucesso. {category_data.name} por {current_user.username}")

@category_router.delete("/delete/{category_id}")
async def delete_category(category_id: int, db_session=Depends(get_db_session), admin_user=Depends(require_admin)):
    """Exclui uma categoria do sistema."""
    category = db_session.query(Category).filter(Category.id == category_id, Category.deleted_at.is_(None)).first()
    if not category: # falta ver se ainda tem produto atribuido a categoria, se tiver, não deixa excluir
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria não encontrada.")
    # Aqui eu aplico um soft delete, para que o sistema saiba quem foi o usuario que removeu
    category.deleted_at = datetime.now(timezone.utc)
    category.deleted_by = admin_user.id  # Supondo que você tenha uma forma de obter o usuário atual
    db_session.commit()
    raise HTTPException(status_code=status.HTTP_200_OK, detail=f"Categoria excluída com sucesso. {category.name} usuario que removeu: {admin_user.username}")

@category_router.patch("/update/{category_id}")
async def update_category(category_id: int, category_data: CategorySchema, db_session=Depends(get_db_session), current_user=Depends(get_current_user)):
    """Atualiza uma categoria existente no sistema."""
    category = db_session.query(Category).filter(Category.id == category_id, Category.deleted_at.is_(None)).first()
    if not category: # Olha se a categoria existe, se não existir, não deixa atualizar e tambem falta verificar se a categoria tem produtos vinculados, se tiver, não deixa atualizar
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria não encontrada.")
    #preciso verificar se o nome novo nao ja existe
    new_name = db_session.query(Category).filter(Category.name == category_data.name, Category.deleted_at.is_(None)).first()
    if new_name is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ja existe uma categoria com esse nome")
    category.name = category_data.name
    category.updated_at = datetime.now(timezone.utc)
    category.updated_by = current_user.id  # Supondo que você tenha uma forma de obter o usuário atual
    db_session.commit()
    raise HTTPException(status_code=status.HTTP_200_OK, detail=f"Categoria atualizada com sucesso. {category.name} usuario que atualizou: {current_user.username}")
