from fastapi import APIRouter, Depends, Query
from app.models import StockMovement, Product, MovementType
from app.dependencies import get_db_session, get_current_user
from sqlalchemy.orm import joinedload
from app.schemas import APIResponse, ProductSchema, StockMovementCreate, StockMovementResponseCreate, StockMovementPaginatedResponseGet
from datetime import date, timezone, datetime, time
from typing import Literal
from app.exceptions import InactiveProductMovementException, ProductNotFoundException, InsufficientStockException, InsufficientStockException

stock_movements_router = APIRouter(prefix="/stock_movement", tags=["stock_movements"])


@stock_movements_router.get("", response_model=APIResponse[StockMovementPaginatedResponseGet])
def list_stock_movements(
    product_id: int | None = Query(
        default=None, description="Filtra por um produto específico"
    ),
    supplier_id: int | None = Query(
        default=None,
        description="Filtra por movimentações de produtos de um fornecedor",
    ),
    user_id: int | None = Query(
        default=None, description="Filtra pelo usuário que realizou a operação"
    ),
    movement_type: Literal["ENTRADA", "SAIDA", "PERDA", "AJUSTE"] | None = Query(
        default=None, description="Tipo de movimentação física"
    ),
    start_date: date | None = Query(
        default=None, description="Data inicial do intervalo (AAAA-MM-DD)"
    ),
    end_date: date | None = Query(
        default=None, description="Data final do intervalo (AAAA-MM-DD)"
    ),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db_session = Depends(get_db_session),
    current_user = Depends(get_current_user),
):
    """Retorna o extrato de movimentações de estoque com filtros combinados."""
    # O joinedload elimina o problema de N+1 queries trazendo produto e usuário no mesmo select
    query = db_session.query(StockMovement).options(
        joinedload(StockMovement.product),
        joinedload(StockMovement.user),
    )

    # 1. Filtro por Produto
    if product_id is not None:
        query = query.filter(StockMovement.product_id == product_id)

    # 2. Filtro por Fornecedor (exige JOIN com Product)
    if supplier_id is not None:
        query = query.join(StockMovement.product).filter(
            Product.supplier_id == supplier_id
        )

    # 3. Filtro por Usuário que executou
    if user_id is not None:
        query = query.filter(StockMovement.created_by == user_id)

    # 4. Filtro por Tipo de Operação
    if movement_type is not None:
        query = query.filter(StockMovement.movement_type == movement_type)

    # 5. Filtros Temporais (convertendo date para limites de timestamp UTC)
    if start_date is not None:
        start_datetime = datetime.combine(
            start_date, time.min, tzinfo=timezone.utc
        )
        query = query.filter(StockMovement.created_at >= start_datetime)

    if end_date is not None:
        end_datetime = datetime.combine(end_date, time.max, tzinfo=timezone.utc)
        query = query.filter(StockMovement.created_at <= end_datetime)

    # Contagem total antes de paginar
    total = query.count()

    # Ordenação estrita: mais recentes primeiro (LIFO)
    offset = (page - 1) * page_size
    movements = (
        query.order_by(StockMovement.created_at.desc(), StockMovement.id.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )

    return APIResponse(message="Busca feita com sucesso" ,data=StockMovementPaginatedResponseGet(
        total=total,
        page=page,
        page_size=page_size,
        items=movements,
    ))

@stock_movements_router.get("/get/{product_id}", response_model=APIResponse[StockMovementPaginatedResponseGet])
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
        raise ProductNotFoundException(product_id=product_id)

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

    return APIResponse(message="Busca feita com sucesso", data=StockMovementPaginatedResponseGet(total=total, page=page, page_size=page_size, items=movements))

@stock_movements_router.post("/create", response_model=APIResponse[StockMovementResponseCreate])
def create_stock_movement(stock_movement: StockMovementCreate, product_id: int, db_session=Depends(get_db_session), current_user=Depends(get_current_user)):
    """Cria uma nova movimentação de estoque no sistema."""
    #preciso checar se o produto existe
    product = db_session.query(Product).filter(Product.id == product_id).with_for_update().first()
    if product is None:
        raise ProductNotFoundException(product_id=product_id)
    elif product.deleted_at is not None:
        raise InactiveProductMovementException(product_id=product.id,product_name=product.name,)
    value_to_shift = stock_movement.quantity

    if stock_movement.movement_type == MovementType.ENTRADA:
        product.stock_quantity += value_to_shift
    elif stock_movement.movement_type in [MovementType.SAIDA, MovementType.PERDA]:
        if product.stock_quantity < value_to_shift:
            type_for_error_msg = ("saida" if MovementType.SAIDA == stock_movement.movement_type else "baixa por perda")
            raise InsufficientStockException(operation_type=type_for_error_msg,available_quantity=product.stock_quantity,requested_quantity=value_to_shift,product_id=product.id,)
        product.stock_quantity -= value_to_shift

    elif stock_movement.movement_type == MovementType.AJUSTE:
        product.stock_quantity = value_to_shift



    # preciso adicionar ou remover a quantia a partir da entrada ou saida
    new_stock_movement = StockMovement(product_id=product.id, quantity=value_to_shift, movement_type=stock_movement.movement_type, created_by= current_user.id, reason=stock_movement.reason)
    db_session.add(new_stock_movement)
    db_session.commit()
    db_session.refresh(new_stock_movement)
    return APIResponse(message = "Movimentacao criada com sucesso",data=StockMovementResponseCreate(id=new_stock_movement.id,
        product_id=new_stock_movement.product_id,
        created_by=new_stock_movement.created_by,
        movement_type=new_stock_movement.movement_type,
        quantity=new_stock_movement.quantity,
        reason=new_stock_movement.reason,
        created_at=new_stock_movement.created_at,
        current_product_stock=product.stock_quantity))
