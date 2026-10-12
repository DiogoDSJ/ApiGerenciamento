from fastapi import APIRouter, Depends, HTTPException, status
from app.models import Category
from app.dependencies import get_db_session, get_current_user
from app.schemas import CategorySchema
from datetime import datetime, timezone

category_router = APIRouter(prefix="/category", tags=["category"])

@category_router.get("/list")
async def return_all_category():
    """Retorna todas as categorias disponíveis no sistema."""
    return {"message": "Lista de todas as categorias disponíveis."}

@category_router.post("/create")
async def create_category(category_data: CategorySchema, db_session=Depends(get_db_session), current_user=Depends(get_current_user)):
    """Cria uma nova categoria no sistema."""
    category = db_session.query(Category).filter(Category.name == category_data.name).first()
    if category:
        if category.deleted_at is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Categoria já existe.")
        else:
            # Se a categoria foi excluída anteriormente, podemos reativá-la
            category.deleted_at = None
            category.deleted_by = None
            category.updated_at = datetime.now(timezone.utc)
            category.updated_by = current_user.id  # Supondo que você tenha uma forma de obter o usuário atual
            db_session.commit()
            raise HTTPException(status_code=status.HTTP_200_OK, detail=f"Categoria reativada com sucesso. {category_data.name} {category_data.created_by}")
    new_category = Category(name=category_data.name, created_by=current_user.id)
    db_session.add(new_category)
    db_session.commit()
    raise HTTPException(status_code=status.HTTP_201_CREATED, detail=f"Categoria criada com sucesso. {category_data.name} {category_data.created_by}")

@category_router.delete("/delete")
async def delete_category(category_data: CategorySchema, db_session=Depends(get_db_session), current_user=Depends(get_current_user)):
    """Exclui uma categoria do sistema."""
    category = db_session.query(Category).filter(Category.name == category_data.name, Category.deleted_at == None).first()
    if not category: # falta ver se ainda tem produto atribuido a categoria, se tiver, não deixa excluir
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria não encontrada.")
    # Aqui eu aplico um soft delete, para que o sistema saiba quem foi o usuario que removeu
    category.deleted_at = datetime.now(timezone.utc)
    category.deleted_by = current_user.id  # Supondo que você tenha uma forma de obter o usuário atual
    db_session.commit()
    raise HTTPException(status_code=status.HTTP_200_OK, detail=f"Categoria excluída com sucesso. {category.name} usuario que removeu: {current_user.username}")

@category_router.post("/update")
async def update_category(category_data: CategorySchema, db_session=Depends(get_db_session), current_user=Depends(get_current_user)):
    """Atualiza uma categoria existente no sistema."""
    category = db_session.query(Category).filter(Category.name == category_data.name, Category.deleted_at == None).first()
    if not category: # Olha se a categoria existe, se não existir, não deixa atualizar e tambem falta verificar se a categoria tem produtos vinculados, se tiver, não deixa atualizar
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria não encontrada.")
    category.name = category_data.name
    category.updated_at = datetime.now(timezone.utc)
    category.updated_by = current_user.id  # Supondo que você tenha uma forma de obter o usuário atual
    db_session.commit()
    raise HTTPException(status_code=status.HTTP_200_OK, detail=f"Categoria atualizada com sucesso. {category.name} usuario que atualizou: {current_user.username}")
