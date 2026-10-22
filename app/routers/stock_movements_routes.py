from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.models import StockMovement, Product, MovementType
from app.dependencies import get_db_session, get_current_user
from app.schemas import ProductSchema, StockMovementCreate, StockMovementResponseCreate, StockMovementPaginatedResponse, StockMovementResponseGet
from datetime import date, timezone, datetime, time

stock_movements_router = APIRouter(prefix="/stock_movement", tags=["stock_movements"])


@stock_movements_router.get("/")
def read_stock_movements():
    """Rota raiz do módulo de movimentações de estoque."""
    return {"message": "Bem-vindo ao módulo de movimentações de estoque!"}

@stock_movements_router.get("/get/{product_id}", response_model=StockMovementPaginatedResponse)
def return_all_stock_movements_from_a_product(product_id: int,
                   movement_type: MovementType | None = Query(default = None, description = "Filtrar por tipo: entrada, saida, perda ou ajuste"),
                   start_date: date | None = Query(default = None, description = "Data inicial da busca"),
                   end_date: date | None = Query(default=None, description = "Data final da busca"),
                   page: int = Query(default = 1, ge= 1, description = "Numero da pagina"),
                   page_size: int = Query(default = 20, ge = 1 , le = 100, description = "Maximo de itens por pagina"),
                   db_session = Depends(get_db_session),
                   current_user = Depends(get_current_user)):
    """Retorna todas as movimentações de estoque de um produto no sistema."""

    product = db_session.query(Product.id).filter(Product.id == product_id).scalar()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto não encontrado.",)

    query = db_session.query(StockMovement).filter(StockMovement.product_id == product_id)

    if movement_type:
        query = query.filter(StockMovement.movement_type == movement_type)

    if start_date:
        start_datetime = datetime.combine(start_date, time.min, tzinfo=timezone.utc)
        query = query.filter(StockMovement.created_at >= start_datetime)

    if end_date:
        end_datetime = datetime.combine(end_date, time.max, tzinfo=timezone.utc)
        query = query.filter(StockMovement.created_at <= end_datetime)

    total = query.count()

    offset = (page - 1) * page_size
    movements = (
        query.order_by(StockMovement.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )

    return StockMovementPaginatedResponse(total=total, page=page, page_size=page_size,product_id=product_id, items=movements)

@stock_movements_router.post("/create", response_model=StockMovementResponseCreate, status_code=status.HTTP_201_CREATED)
def create_stock_movement(stock_movement: StockMovementCreate, product_id: int, db_session=Depends(get_db_session), current_user=Depends(get_current_user)):
    """Cria uma nova movimentação de estoque no sistema."""
    #preciso checar se o produto existe
    product = db_session.query(Product).filter(Product.id == product_id).with_for_update().first()
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Não é possivel movimentar o estoque com um produto que não existe.")
    elif product.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Produto está desativado, nao é possivel movimenta-ló, é necessario reativa-lo")

    value_to_shift = stock_movement.quantity

    if stock_movement.movement_type == MovementType.ENTRADA:
        product.stock_quantity += value_to_shift
    elif stock_movement.movement_type in [MovementType.SAIDA, MovementType.PERDA]:
        if product.stock_quantity < value_to_shift:
            type_for_error_msg = ("saida" if MovementType.SAIDA == stock_movement.movement_type else "baixa por perda")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Estoque insuficiente para {type_for_error_msg}. "f"Disponível: {product.stock_quantity}, Solicitado: {value_to_shift}.")
        product.stock_quantity -= value_to_shift

    elif stock_movement.movement_type == MovementType.AJUSTE:
        product.stock_quantity = value_to_shift



    # preciso adicionar ou remover a quantia a partir da entrada ou saida
    new_stock_movement = StockMovement(product_id=product.id, quantity=value_to_shift, movement_type=stock_movement.movement_type, created_by= current_user.id, reason=stock_movement.reason)
    db_session.add(new_stock_movement)
    db_session.commit()
    db_session.refresh(new_stock_movement)
    return StockMovementResponseCreate(id=new_stock_movement.id,
        product_id=new_stock_movement.product_id,
        created_by=new_stock_movement.created_by,
        movement_type=new_stock_movement.movement_type,
        quantity=new_stock_movement.quantity,
        reason=new_stock_movement.reason,
        created_at=new_stock_movement.created_at,
        current_product_stock=product.stock_quantity)
