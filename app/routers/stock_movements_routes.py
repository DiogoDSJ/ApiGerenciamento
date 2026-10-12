from fastapi import APIRouter, Depends, HTTPException, status
from app.models import StockMovement, Product
from app.dependencies import get_db_session, get_current_user
from app.schemas import StockMovementSchema, ProductSchema


stock_movements_router = APIRouter()


@stock_movements_router.get("/")
async def read_stock_movements():
    """Rota raiz do módulo de movimentações de estoque."""
    return {"message": "Bem-vindo ao módulo de movimentações de estoque!"}

@stock_movements_router.get("/list")
async def return_all_stock_movements():
    """Retorna todas as movimentações de estoque disponíveis no sistema."""
    return {"message": "Lista de todas as movimentações de estoque disponíveis."}

@stock_movements_router.post("/create")
async def create_stock_movement(stock_movement: StockMovementSchema, product_data: ProductSchema, db_session=Depends(get_db_session), current_user=Depends(get_current_user)):
    """Cria uma nova movimentação de estoque no sistema."""
    #preciso checar se o produto existe
    product = db_session.query(Product).filter(Product.sku == product_data.sku).first()
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Não é possivel movimentar o estoque com um produto que não existe.")
    if current_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não existe.")
    if stock_movement:
        #checar se a quantidade vai ficar pra zero
        if stock_movement.movement_type == "entrada":
            # vou chamar uma rota do product para ele mesmo se adicionar, a logica fica melhor
            pass
        else if stock_movement.movement_type == "saida":
            # vou chamar uma rota do product para ele mesmo se remover, a logica fica melhor
            pass
        value_to_shift = 0 #vai depender do retorno acima

    # preciso adicionar ou remover a quantia a partir da entrada ou saida
    new_stock_movement = StockMovement(product_id=product.id, quantity=value_to_shift, movement_type=stock_movement.movement_type, created_by= current_user.id)
    db_session.add(new_stock_movement)
    db_session.commit()
    raise HTTPException(status_code=status.HTTP_201_CREATED, detail = f"Movimentacao concluida com sucesso, tipo da movimentacao: {stock_movement.movement_type}, nova quantia {value_to_shift}.")
