from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.models import Product, Category, Supplier, StockMovement, MovementType
from app.dependencies import get_db_session, get_current_user
from app.schemas import ProductCreate, ProductPaginatedResponse, ProductResponse
from datetime import datetime, timezone
from sqlalchemy import or_

product_router = APIRouter(prefix="/product", tags=["product"])

@product_router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int,db_session = Depends(get_db_session),current_user = Depends(get_current_user)):
    product = (db_session.query(Product).filter(Product.id == product_id, Product.deleted_at.is_(None)).first())
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produto não encontrado.",
        )
    return product


@product_router.get("", response_model=ProductPaginatedResponse)
def search_product(search: str | None = Query(
    default = None, description = "Busca por nome ou SKU"),
                   category_id: int | None = Query(default = None, gt = 0, description = "Filtrar por categoria"),
                   supplier_id: int | None = Query(default = None, gt = 0, description = "Filtrar por fornecedor"),
                   low_stock: bool = Query(default=False, description = "Se verdadeiro, traz os produtos com estoque abaixo do estoque minimo definido daquele produto"),
                   page: int = Query(default = 1, ge= 1, description = "Numero da pagina"),
                   page_size: int = Query(default = 20, ge = 1 , le = 100, description = "Maximo de itens por pagina"),
                   db_session = Depends(get_db_session),
                   current_user = Depends(get_current_user)):

    query = db_session.query(Product).filter(Product.deleted_at.is_(None))

    if search:
        search_term = f"%{search.strip()}%"
        query = query.filter(or_(Product.name.ilike(search_term), (Product.sku.ilike(search_term))))
    if category_id:
        query = query.filter(Product.category_id == category_id)
    if supplier_id:
        query = query.filter(Product.supplier_id == supplier_id)
    if low_stock:
        query = query.filter(Product.minimum_stock >= Product.stock_quantity)

    total = query.count()

    offset = (page - 1) * page_size
    products = query.order_by(Product.name.asc()).offset(offset).limit(page_size).all()
    return ProductPaginatedResponse(total=total, page=page, page_size=page_size, items=products)



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

