from fastapi import APIRouter, Depends, HTTPException, status
from app.models import Product, Category, Supplier, StockMovement, MovementType
from app.dependencies import get_db_session, get_current_user
from app.schemas import ProductCreate
from datetime import datetime, timezone

product_router = APIRouter(prefix="/product", tags=["product"])

@product_router.get("/list")
async def return_all_products():
    """Retorna todos os produtos disponíveis no sistema."""
    return {"message": "Lista de todos os produtos disponíveis."}


@product_router.post("/create")
def create_product(productSchema: ProductCreate, db_session = Depends(get_db_session), current_user = Depends(get_current_user)):
    conflict_conditions = db_session.query(Product).filter(Product.sku == productSchema.sku, Product.deleted_at.is_(None)).first()
    if conflict_conditions and conflict_conditions.sku == productSchema.sku:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Produto com esse sku já existe")
    #verificando se a categoria existe, acho que fornecedor não é obrigatorio, já que o produto pode existir, mas estar sem um fornecedor no momento
    category = db_session.query(Category).filter(Category.id == productSchema.category_id, Category.deleted_at.is_(None)).first()
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail = "Categoria nao encontrada")
    if productSchema.supplier_id is not None:
        supplier = db_session.query(Supplier).filter(Supplier.id == productSchema.supplier_id, Supplier.deleted_at.is_(None)).first()
        if supplier is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail = "Fornecedor nao encontrado")

    new_product = Product(name=productSchema.name, sku=productSchema.sku, cost_price=productSchema.cost_price, sale_price= productSchema.sale_price, minimum_stock = productSchema.minimum_stock, stock_quantity= productSchema.initial_stock, category_id=productSchema.category_id, supplier_id=productSchema.supplier_id, created_by=current_user.id)


    db_session.add(new_product)
    db_session.flush()

    if productSchema.initial_stock > 0:
        first_stock_movement = StockMovement(product_id=new_product.id, quantity=productSchema.initial_stock, movement_type=MovementType.ENTRADA, reason="Quantia inicial cadastrada no estoque.", created_by=current_user.id)
        db_session.add(first_stock_movement)

    db_session.commit()
    db_session.refresh(new_product)
    return new_product




