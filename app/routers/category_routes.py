from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.models import Category, Product
from app.dependencies import get_db_session, get_current_user, require_admin
from app.schemas import CategorySchema, CategoryPaginatedResponse, APIResponse, CategoryResponse
from sqlalchemy import exists, func, or_
from datetime import datetime, timezone
from typing import Literal
from app.exceptions import CategoryNotFoundException, CategoryAlreadyExistsException, CategoryHasProductsExcetion

category_router = APIRouter(prefix="/category", tags=["category"])

@category_router.get("/{category_id}", response_model=APIResponse[CategoryResponse])
def get_category(category_id: int,db_session = Depends(get_db_session),current_user = Depends(get_current_user)):
    category = (db_session.query(Category).filter(Category.id == category_id).first())
    if not category:
        raise CategoryNotFoundException(identifier=category_id)
    return APIResponse(message="Categoria encontrada com sucesso", data = category)

@category_router.get("", response_model=APIResponse[CategoryPaginatedResponse])
def search_category(search: str | None = Query(default = None, description = "Busca por nome de categoria"),
                              status_filter: Literal["active", "inactive", "all"] = Query(default="active", description="Filtro de estado: 'active' (padrão), 'inactive' (desativados) ou 'all' (todos)"),
                              db_session=Depends(get_db_session),
                              page: int = Query(default = 1, ge= 1, description = "Numero da pagina"),
                              page_size: int = Query(default = 20, ge = 1 , le = 100, description = "Maximo de itens por pagina"),
                              current_user=Depends(get_current_user)):
    """Retorna todas as categorias disponíveis no sistema."""
    query = db_session.query(Category)
    if status_filter == "active":
        query = query.filter(Category.deleted_at.is_(None))
    elif status_filter == "inactive":
        query = query.filter(Category.deleted_at.is_not(None))
    if search:
            search_term = f"%{search.strip()}%"
            query = query.filter(or_(Category.name.ilike(search_term)))

    total = query.count()

    offset = (page - 1) * page_size
    categorys = query.order_by(Category.name.asc()).offset(offset).limit(page_size).all()
    return APIResponse(message = "Abaixo estao o resultado da busca que foi concluida", data=CategoryPaginatedResponse(total=total, page=page, page_size=page_size, items=categorys))

@category_router.post("/create", response_model=APIResponse[CategoryResponse])
def create_category(category_data: CategorySchema, db_session=Depends(get_db_session), current_user=Depends(get_current_user)):
    """Cria uma nova categoria no sistema."""
    category = db_session.query(Category).filter(Category.name == category_data.name).first()
    if category:
        raise CategoryAlreadyExistsException(category_name=category.name, category_id=category.id)
    new_category = Category(name=category_data.name, created_by=current_user.id)
    db_session.add(new_category)
    db_session.commit()
    return APIResponse(message="Categoria criada com sucesso", data = new_category)

@category_router.delete("/delete/{category_id}", response_model=APIResponse[CategoryResponse])
def delete_category(category_id: int, db_session=Depends(get_db_session), admin_user=Depends(require_admin)):
    """Exclui uma categoria do sistema."""
    category = db_session.query(Category).filter(Category.id == category_id, Category.deleted_at.is_(None)).first()
    if not category:
        raise CategoryNotFoundException(identifier=category_id)
    category_check = db_session.query(exists().where(Product.category_id == category_id, Product.deleted_at.is_(None))).scalar()
    if category_check:
        raise CategoryHasProductsExcetion(category=category.name)
    # Aqui eu aplico um soft delete, para que o sistema saiba quem foi o usuario que removeu
    category.deleted_at = datetime.now(timezone.utc)
    category.deleted_by = admin_user.id  # Supondo que você tenha uma forma de obter o usuário atual
    db_session.commit()
    return APIResponse(message="Categoria desativada com sucesso", data = category)

@category_router.patch("/restore/{category_id}", response_model=APIResponse[CategoryResponse])
def restore_category(category_id: int, db_session=Depends(get_db_session), admin_user=Depends(require_admin)):
    """Reativa uma categoria do sistema."""
    category = db_session.query(Category).filter(Category.id == category_id, Category.deleted_at.is_not(None)).first()
    if not category: # falta ver se ainda tem produto atribuido a categoria, se tiver, não deixa excluir
        raise CategoryNotFoundException(identifier=category_id)
    collision = (db_session.query(Category).filter(Category.id != category.id,Category.deleted_at.is_(None),func.lower(Category.name) == category.name.lower().strip(),).first())
    if collision:
        raise CategoryAlreadyExistsException(category_name=category.name, category_id=category.id)

    category.deleted_at = None
    category.deleted_by_id = None
    category.updated_by_id = admin_user.id

    db_session.commit()
    db_session.refresh(category)

    return APIResponse(message="Categoria restaurada com sucesso", data = category)


@category_router.patch("/update/{category_id}", response_model=APIResponse[CategoryResponse])
def update_category(category_id: int, category_data: CategorySchema, db_session=Depends(get_db_session), current_user=Depends(get_current_user)):
    """Atualiza uma categoria existente no sistema."""
    category = db_session.query(Category).filter(Category.id == category_id).first()
    if not category: # Olha se a categoria existe, se não existir, não deixa atualizar e tambem falta verificar se a categoria tem produtos vinculados, se tiver, não deixa atualizar
        raise CategoryNotFoundException(identifier=category_id)
    #preciso verificar se o nome novo nao ja existe
    new_name = db_session.query(Category).filter(Category.name == category_data.name).first()
    if new_name is not None:
        raise CategoryAlreadyExistsException(category_name=category.name, category_id=category.id)
    category.name = category_data.name
    category.updated_at = datetime.now(timezone.utc)
    category.updated_by = current_user.id  # Supondo que você tenha uma forma de obter o usuário atual
    db_session.commit()
    return APIResponse(message="Categoria atualizada com sucesso", data = category)
