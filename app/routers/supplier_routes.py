from fastapi import APIRouter, Depends, HTTPException, status
from app.dependencies import get_current_user, get_db_session, require_admin
from app.models import Supplier
from app.schemas import SupplierSchema
from datetime import datetime, timezone

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
    filter1 = db_session.query(Supplier).filter(Supplier.cnpj == supplier_data.cnpj, Supplier.deleted_at.is_(None)).first()
    if filter1 is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ja existe uma empresa com esse CNPJ")
    filter2 = db_session.query(Supplier).filter(Supplier.email == supplier_data.email, Supplier.deleted_at.is_(None)).first()
    if filter2 is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ja existe uma empresa com esse email")

    supplier.name = supplier_data.name
    supplier.email = supplier_data.email
    supplier.phone = supplier_data.phone
    supplier.address = supplier_data.address
    supplier.cnpj = supplier_data.cnpj
    supplier.updated_at = datetime.now(timezone.utc)
    supplier.updated_by = current_user.id  # Supondo que você tenha uma forma de obter o usuário atual
    db_session.commit()
    raise HTTPException(status_code=status.HTTP_200_OK, detail=f"Fornecedor atualizado com sucesso. {supplier.name} usuario que atualizou: {current_user.username}")

