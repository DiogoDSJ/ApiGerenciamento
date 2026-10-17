from fastapi import APIRouter, Depends, HTTPException, status
from app.dependencies import get_current_user, get_db_session, require_admin
from app.models import Supplier
from app.schemas import SupplierSchema
from datetime import datetime, timezone
from sqlalchemy import or_

supplier_router = APIRouter(prefix="/supplier", tags=["supplier"])


@supplier_router.get("/list")
async def return_all_supplier(skip:int=0, limit:int = 100, db_session=Depends(get_db_session), current_user=Depends(get_current_user)):
    """Retorna todas as fornecedores disponíveis no sistema."""
    suppliers = (db_session.query(Supplier).filter(Supplier.deleted_at.is_(None)).offset(skip).limit(limit).all())
    return suppliers


@supplier_router.post("/create")
async def create_supplier(supplier_data: SupplierSchema, db_session=Depends(get_db_session), current_user=Depends(get_current_user)):
    """Cria um fornecedor"""
    supplier = db_session.query(Supplier).filter(Supplier.cnpj == supplier_data.cnpj, Supplier.deleted_at.is_(None)).first()
    if supplier:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Fornecedor já existe.")
    supplier1 = db_session.query(Supplier).filter(Supplier.email == supplier_data.email, Supplier.deleted_at.is_(None)).first()
    if supplier1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Fornecedor com esse email  já existe.")
    new_supplier = Supplier(name=supplier_data.name, cnpj=supplier_data.cnpj, email=supplier_data.email, phone=supplier_data.phone, address=supplier_data.address, created_by=current_user.id)
    db_session.add(new_supplier)
    db_session.commit()
    raise HTTPException(status_code=status.HTTP_201_CREATED, detail=f"Fornecedor criada com sucesso. {supplier_data.name} por {current_user.username}")

@supplier_router.delete("/delete/{supplier_id}")
async def delete_supplier(supplier_id: int, db_session=Depends(get_db_session), admin_user=Depends(require_admin)):
    """Exclui um fornecedor"""
    supplier = db_session.query(Supplier).filter(Supplier.id == supplier_id, Supplier.deleted_at.is_(None)).first()
    if not supplier:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fornecedor não encontrado.")
    supplier.deleted_at = datetime.now(timezone.utc)
    supplier.deleted_by = admin_user.id  # Supondo que você tenha uma forma de obter o usuário atual
    db_session.commit()
    raise HTTPException(status_code=status.HTTP_200_OK, detail=f"Fornecedor excluído com sucesso. {Supplier.name} usuario que removeu: {admin_user.username}")


@supplier_router.patch("/update/{supplier_id}")
async def update_supplier(supplier_id: int, supplier_data: SupplierSchema, db_session=Depends(get_db_session), current_user=Depends(get_current_user)):
    """Atualiza uma categoria existente no sistema."""
    supplier = db_session.query(Supplier).filter(Supplier.id == supplier_id, Supplier.deleted_at.is_(None)).first()
    if not supplier: # Olha se a categoria existe, se não existir, não deixa atualizar e tambem falta verificar se a categoria tem produtos vinculados, se tiver, não deixa atualizar
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria não encontrada.")
    #preciso verificar se o nome novo nao ja existe

    conflict_conditions = []


    if (supplier_data.name is not None and supplier_data.name != supplier.name):
        conflict_conditions.append(Supplier.name == supplier_data.name)
    if (supplier_data.email is not None and supplier_data.email != supplier.email):
        conflict_conditions.append(Supplier.email == supplier_data.email)
    if (supplier_data.phone is not None and supplier_data.phone != supplier.phone):
            conflict_conditions.append(Supplier.phone == supplier_data.phone)

    if conflict_conditions:
        conflict_supplier = db_session.query(Supplier).filter(Supplier.id != supplier.id, Supplier.deleted_at.is_(None),or_(*conflict_conditions),).first()
        if conflict_supplier:
            if conflict_supplier.name == supplier_data.name:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Nome ja em uso")
            if conflict_supplier.email == supplier_data.email:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email ja em uso")
            if conflict_supplier.phone == supplier_data.phone:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Telefone ja em uso")


    update_dict = supplier_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(supplier, field, value)

    supplier.updated_by = current_user.id  # Supondo que você tenha uma forma de obter o usuário atual
    db_session.commit()
    db_session.refresh(supplier)
    return supplier

