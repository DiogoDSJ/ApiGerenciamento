from fastapi import APIRouter, Depends, HTTPException, status
from app.dependencies import get_current_user, get_db_session
from app.models import Supplier
from app.schemas import SupplierSchema
from datetime import datetime, timezone

supplier_router = APIRouter(prefix="/supplier", tags=["supplier"])


@supplier_router.get("/list")
async def return_all_supplier(skip:int=0, limit:int = 100, db_session=Depends(get_db_session), current_user=Depends(get_current_user)):
    """Retorna todas as fornecedores disponíveis no sistema."""
    suppliers = (db_session.query(Supplier).filter(Supplier.deleted_at.is_(None)).offset(skip).limit(limit).all())
    return suppliers

    name: str
    cnpj: str
    email: str
    phone: str
    address: str


@supplier_router.post("/create")
async def create_supplier(supplier_data: SupplierSchema, db_session=Depends(get_db_session), current_user=Depends(get_current_user)):
    """Cria um fornecedor"""
    supplier = db_session.query(Supplier).filter(Supplier.cnpj == supplier_data.cnpj, Supplier.deleted_at.is_(None)).first()
    if supplier:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Fornecedor já existe.")
    new_supplier = Supplier(name=supplier_data.name, cnpj=supplier_data.cnpj, email=supplier_data.email, phone=supplier_data.phone, address=supplier_data.address, created_by=current_user.id)
    db_session.add(new_supplier)
    db_session.commit()
    raise HTTPException(status_code=status.HTTP_201_CREATED, detail=f"Fornecedor criada com sucesso. {supplier_data.name} por {current_user.username}")

