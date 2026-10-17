from fastapi import APIRouter, Depends, HTTPException, status
from app.models import Product, Category, Supplier
from app.dependencies import get_db_session, get_current_user
from app.schemas import ProductSchema
from datetime import datetime, timezone

product_router = APIRouter(prefix="/product", tags=["product"])

@product_router.get("/list")
async def return_all_products():
    """Retorna todos os produtos disponíveis no sistema."""
    return {"message": "Lista de todos os produtos disponíveis."}


@product_router.post("/create")
async def create_product(productSchema: ProductSchema, db_session = Depends(get_db_session), current_user = Depends(get_current_user)):
    get_product = db_session.query(Product).filter((Product.sku == productSchema.sku, Product.deleted_at.is_(None))).first()
    if get_product.sku == productSchema.sku:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Produto com esse sku já existe")

    #verificando se a categoria existe, acho que fornecedor não é obrigatorio, já que o produto pode existir, mas estar sem um fornecedor no momento
    category = db_session.query(Category).filter((Category.id == productSchema.category_id, Category.deleted_at.is_(None))).first()
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail = "Categoria nao encontrada")

    if productSchema.cost_price < 0:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail = "O valor de custo deve ser zero ou maior que zero")
    elif productSchema.sale_price < 0:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail = "O valor de venda deve ser zero ou maior que zero")
    elif productSchema.minimum_stock < 0:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail = "O valor de estoque minimo deve ser zero ou maior que zero")
    elif productSchema.stock_quantity < 0:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail = "A quantia de estoque deve ser zero ou maior que zero")
    new_product = Product(name=productSchema.name, sku=productSchema.sku, cost_price=productSchema.cost_price, sale_price= productSchema.sale_price, minimum_stock = productSchema.minimum_stock, stock_quantity= productSchema.stock_quantity, category_id=productSchema.category_id, supplier_id=productSchema.supplier_id, created_by=current_user.id)
    db_session.add(new_product)
    db_session.commit()
    raise HTTPException(status_code=status.HTTP_201_CREATED, detail=f"Produto criada com sucesso. {new_product.name} {new_product.created_by}")





## para criar uma rota de adicionar quantidades de produto eu preciso mexer com os stocksmovemnts pelo jeito, trabalho da dis viu
