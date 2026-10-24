from datetime import datetime, timezone
from app.models import MovementType, StockMovement


def test_create_stock_movement_entrada_success(
    client, test_product, db_session
):
    """Entrada física: soma ao estoque e registra histórico."""
    payload = {
        "product_id": test_product.id,
        "quantity": 5,
        "movement_type": "entrada",
        "reason": "Compra de reposicao",
    }

    response = client.post(
        f"/stock_movement/create?product_id={test_product.id}",
        json=payload,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["current_product_stock"] == 15
    assert body["data"]["movement_type"] == "entrada"

    db_session.refresh(test_product)
    assert test_product.stock_quantity == 15


def test_create_stock_movement_saida_success(client, test_product, db_session):
    """Saída permitida: debita do estoque existente."""
    payload = {
        "product_id": test_product.id,
        "quantity": 4,
        "movement_type": "saida",
        "reason": "Venda presencial balcao",
    }

    response = client.post(
        f"/stock_movement/create?product_id={test_product.id}",
        json=payload,
    )

    assert response.status_code == 200
    assert response.json()["data"]["current_product_stock"] == 6

    db_session.refresh(test_product)
    assert test_product.stock_quantity == 6


def test_create_stock_movement_insufficient_stock_fails(client, test_product):
    """Saída superior ao saldo disponível deve retornar 400 com InsufficientStockException."""
    payload = {
        "product_id": test_product.id,
        "quantity": 20,  # Estoque inicial é 10
        "movement_type": "saida",
        "reason": "Tentativa de saida sem saldo",
    }

    response = client.post(
        f"/stock_movement/create?product_id={test_product.id}",
        json=payload,
    )

    assert response.status_code == 400
    body = response.json()
    assert body["success"] is False
    assert body["error_code"] == "INSUFFICIENT_STOCK"
    assert body["details"]["available_quantity"] == 10
    assert body["details"]["requested_quantity"] == 20


def test_create_stock_movement_inactive_product_fails(
    client, test_product, test_admin_user, db_session
):
    """Produto em soft delete não pode ser movimentado."""
    test_product.deleted_at = datetime.now(timezone.utc)
    test_product.deleted_by = test_admin_user.id
    db_session.commit()

    payload = {
        "product_id": test_product.id,
        "quantity": 2,
        "movement_type": "entrada",
        "reason": "Tentativa indevida",
    }

    response = client.post(
        f"/stock_movement/create?product_id={test_product.id}",
        json=payload,
    )

    assert response.status_code == 400
    assert (
        response.json()["error_code"] == "INACTIVE_PRODUCT_MOVEMENT_BLOCKED"
    )


def test_create_stock_movement_product_not_found_fails(client):
    """Produto inexistente deve retornar 404."""
    payload = {
        "product_id": 999999,
        "quantity": 1,
        "movement_type": "entrada",
    }

    response = client.post(
        "/stock_movement/create?product_id=999999",
        json=payload,
    )

    assert response.status_code == 404
    assert response.json()["error_code"] == "PRODUCT_NOT_FOUND"


def test_list_stock_movements_pagination(
    client, test_product, test_admin_user, db_session
):
    """Extrato paginado geral de movimentações."""
    m1 = StockMovement(
        product_id=test_product.id,
        quantity=3,
        movement_type=MovementType.ENTRADA,
        reason="Entrada A",
        created_by=test_admin_user.id,
    )
    m2 = StockMovement(
        product_id=test_product.id,
        quantity=1,
        movement_type=MovementType.SAIDA,
        reason="Saida B",
        created_by=test_admin_user.id,
    )
    db_session.add_all([m1, m2])
    db_session.commit()

    response = client.get("/stock_movement?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] == 2
    assert len(data["items"]) == 2


def test_get_stock_movements_from_product(
    client, test_product, test_admin_user, db_session
):
    """Busca de movimentações isoladas de um produto específico."""
    m = StockMovement(
        product_id=test_product.id,
        quantity=7,
        movement_type=MovementType.ENTRADA,
        reason="Lote recebido",
        created_by=test_admin_user.id,
    )
    db_session.add(m)
    db_session.commit()

    response = client.get(f"/stock_movement/get/{test_product.id}")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] == 1
    assert data["items"][0]["quantity"] == 7
