from fastapi import APIRouter, Depends, HTTPException, status
from app.models import Product
from app.dependencies import get_db_session, get_current_user
from app.schemas import ProductSchema

product_router = APIRouter(prefix="/product", tags=["product"])

@product_router.get("/list")
async def return_all_products():
    """Retorna todos os produtos disponíveis no sistema."""
    return {"message": "Lista de todos os produtos disponíveis."}


@product_router.post("/create")
async def create_product(productSchema: ProductSchema, db_session = Depends(get_db_session), current_user = Depends(get_current_user)):
    product = db_session.query(Product).filter((Product.sku == productSchema.sku)).first()
    if product:
        if product.deleted_at is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Produto com esse sku já existe")
        else:
            product.deleted_at = None
            product.updated_at = None
            product.updated_at = datetime.now(timezone.utc)
            product.updated_by = current_user.id  # Supondo que você tenha uma forma de obter o usuário atual
            db_session.commit()
            raise HTTPException(status_code=status.HTTP_200_OK, detail=f"Produto reativada com sucesso. {product.name} {product.created_by}")
    new_product = product(name=product.name, created_by=current_user.id)
    db_session.add(new_product)
    db_session.commit()
    raise HTTPException(status_code=status.HTTP_201_CREATED, detail=f"Produto criada com sucesso. {product.name} {product.created_by}")



## para criar uma rota de adicionar quantidades de produto eu preciso mexer com os stocksmovemnts pelo jeito, trabalho da dis viu
