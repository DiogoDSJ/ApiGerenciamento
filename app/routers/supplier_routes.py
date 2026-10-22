from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.dependencies import get_current_user, get_db_session, require_admin
from app.models import Supplier, Product
from app.schemas import SupplierSchema, SupplierResponse, SupplierPaginatedResponse
from datetime import datetime, timezone
from sqlalchemy import or_, exists, func
from typing import Literal

supplier_router = APIRouter(prefix="/supplier", tags=["supplier"])


@supplier_router.get("/{supplier_id}")
def get_supplier(supplier_id: int,db_session = Depends(get_db_session),current_user = Depends(get_current_user)):
    supplier = (db_session.query(Supplier).filter(Supplier.id == supplier_id).first())
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fornecedor não encontrado.",
        )
    return supplier

@supplier_router.get("")
def search_supplier(search: str | None = Query(default = None, description = "Busca por nome de fornecedor, cnpj, email ou telefone"),
                              status_filter: Literal["active", "inactive", "all"] = Query(default="active", description="Filtro de estado: 'active' (padrão), 'inactive' (desativados) ou 'all' (todos)"),
                              db_session=Depends(get_db_session),
                              page: int = Query(default = 1, ge= 1, description = "Numero da pagina"),
                              page_size: int = Query(default = 20, ge = 1 , le = 100, description = "Maximo de itens por pagina"),
                              current_user=Depends(get_current_user)):
    """Retorna todas os fornecedores disponíveis no sistema."""
    query = db_session.query(Supplier)
    if status_filter == "active":
        query = query.filter(Supplier.deleted_at.is_(None))
    elif status_filter == "inactive":
        query = query.filter(Supplier.deleted_at.is_not(None))
    if search:
        search_term = f"%{search.strip()}%"
        query = query.filter(or_(Supplier.name.ilike(search_term), Supplier.cnpj.ilike(search_term), Supplier.phone.ilike(search_term), Supplier.email.ilike(search_term)))

    total = query.count()

    offset = (page - 1) * page_size
    suppliers = query.order_by(Supplier.name.asc()).offset(offset).limit(page_size).all()
    return SupplierPaginatedResponse(total=total, page=page, page_size=page_size, items=suppliers)


@supplier_router.post("/create")
def create_supplier(supplier_data: SupplierSchema, db_session=Depends(get_db_session), current_user=Depends(get_current_user)):
    """Cria um fornecedor"""
    supplier = db_session.query(Supplier).filter(Supplier.cnpj == supplier_data.cnpj).first()
    if supplier:
        if supplier.deleted_at is None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Fornecedor com esse cnpj já existe.")
        else:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Fornecedor com esse cnpj já existe, porem esta desativada, para usa-la, reative em vez de criar outra, id {supplier.id}")
    supplier1 = db_session.query(Supplier).filter(Supplier.email == supplier_data.email, Supplier.deleted_at.is_(None)).first()
    if supplier1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Fornecedor com esse email  já existe.")
    new_supplier = Supplier(name=supplier_data.name, cnpj=supplier_data.cnpj, email=supplier_data.email, phone=supplier_data.phone, address=supplier_data.address, created_by=current_user.id)
    db_session.add(new_supplier)
    db_session.commit()
    raise HTTPException(status_code=status.HTTP_201_CREATED, detail=f"Fornecedor criada com sucesso. {supplier_data.name} por {current_user.username}")

@supplier_router.delete("/delete/{supplier_id}")
def delete_supplier(supplier_id: int, db_session=Depends(get_db_session), admin_user=Depends(require_admin)):
    """Exclui um fornecedor"""
    supplier = db_session.query(Supplier).filter(Supplier.id == supplier_id, Supplier.deleted_at.is_(None)).first()
    if not supplier:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fornecedor não encontrado.")
    supplier_check = db_session.query(exists().where(Product.supplier_id == supplier_id, Product.deleted_at.is_(None))).scalar()
    if supplier_check:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nao é possivel deletar essa categoria, pois tem produtos ativos anexados a ela.")
    supplier.deleted_at = datetime.now(timezone.utc)
    supplier.deleted_by = admin_user.id  # Supondo que você tenha uma forma de obter o usuário atual
    db_session.commit()
    db_session.refresh(supplier)
    return supplier

@supplier_router.patch("/restore/{supplier_id}")
def restore_supplier(supplier_id, db_session= Depends(get_db_session), admin_user = Depends(require_admin)):
    supplier = db_session.query(Supplier).filter(Supplier.id == supplier_id, Supplier.deleted_at.is_not(None)).first()
    if not supplier:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fornecedor não encontrada para restauracao")

    conflicts = (db_session.query(Supplier).filter(Supplier.id != supplier_id, or_(Supplier.cnpj == supplier.cnpj,Supplier.email == supplier.email, Supplier.phone == supplier.phone,func.lower(Supplier.name) == supplier.name.strip().lower(),),).all())
    if conflicts:
        details = [f"ID {c.id} ({c.name})" for c in conflicts]
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Não é possível restaurar. Há conflito de dados com o(s) "
                f"fornecedor(es): {', '.join(details)}."
            ),
        )

    supplier.deleted_at = None
    supplier.deleted_by_id = None
    supplier.updated_by_id = admin_user.id

    db_session.commit()
    db_session.refresh(supplier)

    return supplier



@supplier_router.patch("/update/{supplier_id}")
def update_supplier(supplier_id: int, supplier_data: SupplierSchema, db_session=Depends(get_db_session), current_user=Depends(get_current_user)):
    """Atualiza um fornecedor existente no sistema."""
    supplier = db_session.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier: # Olha se a categoria existe, se não existir, não deixa atualizar e tambem falta verificar se a categoria tem produtos vinculados, se tiver, não deixa atualizar
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fornecedor não encontrada.")
    #preciso verificar se o nome novo nao ja existe

    conflict_conditions = []


    if (supplier_data.name is not None and supplier_data.name != supplier.name):
        conflict_conditions.append(Supplier.name == supplier_data.name)
    if (supplier_data.email is not None and supplier_data.email != supplier.email):
        conflict_conditions.append(Supplier.email == supplier_data.email)
    if (supplier_data.phone is not None and supplier_data.phone != supplier.phone):
        conflict_conditions.append(Supplier.phone == supplier_data.phone)
    if (supplier_data.cnpj is not None and supplier_data.cnpj != supplier.cnpj):
        conflict_conditions.append(Supplier.cnpj == supplier_data.cnpj)

    if conflict_conditions:
        conflict_supplier = db_session.query(Supplier).filter(Supplier.id != supplier.id,or_(*conflict_conditions),).first()
        if conflict_supplier:
            if conflict_supplier.name == supplier_data.name:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Nome ja em uso")
            if conflict_supplier.email == supplier_data.email:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email ja em uso")
            if conflict_supplier.phone == supplier_data.phone:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Telefone ja em uso")
            if conflict_supplier.cnpj == supplier_data.cnpj:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="CNPJ ja em uso")


    update_dict = supplier_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(supplier, field, value)

    supplier.updated_by = current_user.id  # Supondo que você tenha uma forma de obter o usuário atual
    db_session.commit()
    db_session.refresh(supplier)
    return supplier

