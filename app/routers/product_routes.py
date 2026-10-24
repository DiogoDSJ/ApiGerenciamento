from fastapi import APIRouter, Depends, Query
from app.models import Product, Category, Supplier, StockMovement, MovementType
from app.dependencies import get_db_session, get_current_user
from app.schemas import ProductCreate, ProductPaginatedResponse, ProductResponse, ProductUpdate, APIResponse
from datetime import datetime, timezone
from sqlalchemy import or_
from typing import Literal
from app.exceptions import SupplierNotActivedException, CategoryNotActivedException, ProductStillHaveStockException, SupplierNotFoundException, CategoryNotFoundException, ProductNotFoundException, ProductConflictException, ProductSKUConflictException

product_router = APIRouter(prefix="/product", tags=["product"])

@product_router.get("/{product_id}", response_model = APIResponse[ProductResponse])
def get_product(product_id: int,db_session = Depends(get_db_session),current_user = Depends(get_current_user)):
    """Acha um produto pelo id e retorna suas informacoes"""
    product = (db_session.query(Product).filter(Product.id == product_id, Product.deleted_at.is_(None)).first())
    if not product:
        raise ProductNotFoundException(product_id=product_id)
    return APIResponse(message="Busca concluida com sucesso", data = product)



@product_router.get("", response_model = APIResponse[ProductPaginatedResponse])
def search_product(search: str | None = Query(default = None, description = "Busca por nome ou SKU"),
                   category_id: int | None = Query(default = None, gt = 0, description = "Filtrar por categoria"),
                   supplier_id: int | None = Query(default = None, gt = 0, description = "Filtrar por fornecedor"),
                   low_stock: bool = Query(default=False, description = "Se verdadeiro, traz os produtos com estoque abaixo do estoque minimo definido daquele produto"),
                   page: int = Query(default = 1, ge= 1, description = "Numero da pagina"),
                   page_size: int = Query(default = 20, ge = 1 , le = 100, description = "Maximo de itens por pagina"),
                   status_filter: Literal["active", "inactive", "all"] = Query(default="active",
                    description="Filtro de estado: 'active' (padrão), 'inactive' (desativados) ou 'all' (todos)"),
                   db_session = Depends(get_db_session),
                   current_user = Depends(get_current_user)):
    """Procura a partir de queries informacoes de produtos cadastrados no sistema"""
    query = db_session.query(Product)

    if status_filter == "active":
        query = query.filter(Product.deleted_at.is_(None))
    elif status_filter == "inactive":
        query = query.filter(Product.deleted_at.is_not(None))

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
    return APIResponse(message="Busca concluida com sucesso", data = ProductPaginatedResponse(total=total, page=page, page_size=page_size, items=products))




@product_router.post("/create", response_model = APIResponse[ProductResponse])
def create_product(productSchema: ProductCreate, db_session = Depends(get_db_session), current_user = Depends(get_current_user)):
    """Cria um produto e o retorna"""
    conflict_conditions = db_session.query(Product).filter(Product.sku == productSchema.sku).first()
    if conflict_conditions and conflict_conditions.sku == productSchema.sku:
        if conflict_conditions.deleted_at is not None:
            raise ProductSKUConflictException(sku=conflict_conditions.sku, existing_id=conflict_conditions.id)
        else:
            raise ProductSKUConflictException(sku=conflict_conditions.sku, existing_id=conflict_conditions.id, is_inactive=True)
    #verificando se a categoria existe, acho que fornecedor não é obrigatorio, já que o produto pode existir, mas estar sem um fornecedor no momento
    category = db_session.query(Category).filter(Category.id == productSchema.category_id, Category.deleted_at.is_(None)).first()
    if category is None:
        raise CategoryNotFoundException(identifier=productSchema.category_id)
    if productSchema.supplier_id is not None:
        supplier = db_session.query(Supplier).filter(Supplier.id == productSchema.supplier_id, Supplier.deleted_at.is_(None)).first()
        if supplier is None:
            raise SupplierNotFoundException(supplier_id = productSchema.supplier_id)

    new_product = Product(name=productSchema.name, sku=productSchema.sku, cost_price=productSchema.cost_price, sale_price= productSchema.sale_price, minimum_stock = productSchema.minimum_stock, stock_quantity= productSchema.initial_stock, category_id=productSchema.category_id, supplier_id=productSchema.supplier_id, created_by=current_user.id)


    db_session.add(new_product)
    db_session.flush()

    if productSchema.initial_stock > 0:
        first_stock_movement = StockMovement(product_id=new_product.id, quantity=productSchema.initial_stock, movement_type=MovementType.ENTRADA, reason="Quantia inicial cadastrada no estoque.", created_by=current_user.id)
        db_session.add(first_stock_movement)

    db_session.commit()
    db_session.refresh(new_product)
    return APIResponse(message="Produto criado com sucesso", data = new_product)


@product_router.patch("/modify", response_model = APIResponse[ProductResponse])
def modify_product(product_id: int, product_data: ProductUpdate, db_session = Depends(get_db_session), current_user = Depends(get_current_user)):
    """Modifica um produto sendo ele ativo ou inativo e retorna o mesmo"""
    product = db_session.query(Product).filter(Product.deleted_at.is_(None), Product.id == product_id).first()
    if not product:
        raise ProductNotFoundException(product_id=product_id)
    update_data = product_data.model_dump(exclude_unset=True)
    new_sku = update_data.get("sku")
    if new_sku:
        product_query = db_session.query(Product).filter(Product.id != product.id, Product.sku == new_sku).first()
        if(product_query):
            if product_query.deleted_at is None:
                raise ProductSKUConflictException(sku=product_query.sku, existing_id=product_query.id)
            else:
                raise ProductSKUConflictException(sku=product_query.sku, existing_id=product_query.id, is_inactive=True)
    new_category = update_data.get("category_id")
    new_supplier = update_data.get("supplier_id")
    if new_category is not None:
        category = db_session.query(Category).filter(Category.id == new_category, Category.deleted_at.is_(None)).first()
        if category is None:
            raise CategoryNotFoundException(identifier=new_category)
    if new_supplier is not None:
        supplier = db_session.query(Supplier).filter(Supplier.id == new_supplier, Supplier.deleted_at.is_(None)).first()
        if supplier is None:
            raise SupplierNotFoundException(supplier_id = new_supplier)

    for field, value in update_data.items():
        setattr(product, field, value)

    product.updated_by = current_user.id
    db_session.commit()
    db_session.refresh(product)
    return APIResponse(message="Produto editado com sucesso", data = product)

@product_router.delete("/delete/{product_id}", response_model = APIResponse[ProductResponse])
def delete_product(product_id: int, db_session=Depends(get_db_session), current_user=Depends(get_current_user)):
    """Exclui um produto do sistema"""
    product = db_session.query(Product).filter(Product.id == product_id, Product.deleted_at.is_(None)).first()
    if not product:
        raise ProductNotFoundException(product_id=product_id)
    if product.stock_quantity > 0:
        raise ProductStillHaveStockException(product=product.name)

    product.deleted_at = datetime.now(timezone.utc)
    product.deleted_by = current_user.id
    db_session.commit()
    return APIResponse(message="Produto desativado com sucesso", data = product)


@product_router.patch("/restore/{product_id}", response_model = APIResponse[ProductResponse])
def restore_product(product_id: int, db_session=Depends(get_db_session), current_user=Depends(get_current_user)):
    """Restaura um produto do sistema"""
    product = db_session.query(Product).filter(Product.id == product_id, Product.deleted_at.is_not(None)).first()
    if not product:
        raise ProductNotFoundException(product_id=product_id, is_inactive=True)
    product_verify_sku = db_session.query(Product).filter(Product.sku == product.sku, Product.deleted_at.is_(None), Product.id != product_id).first()
    if product_verify_sku:
        raise ProductSKUConflictException(sku=product_verify_sku.sku, existing_id=product_verify_sku.id)
    category_is_active = (db_session.query(Category.id).filter(Category.id == product.category_id, Category.deleted_at.is_(None)).scalar())


    if not category_is_active:
        raise CategoryNotActivedException(category_name = "", category_id=product.category_id)

    # 3. Validação do Fornecedor vinculado (se houver, deve estar ativo)
    if product.supplier_id is not None:
        supplier_is_active = (db_session.query(Supplier.id).filter(Supplier.id == product.supplier_id,Supplier.deleted_at.is_(None),).scalar())
        if not supplier_is_active:
            raise SupplierNotActivedException(supplier_name=supplier_is_active.name, supplier_id=supplier_is_active.id)


    product.deleted_at = None
    product.deleted_by_id = None
    product.updated_by_id = current_user.id

    db_session.commit()
    db_session.refresh(product)
    return APIResponse(message="Produto resutarado com sucesso", data = product)

