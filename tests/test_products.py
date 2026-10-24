from datetime import datetime, timezone
from app.models import MovementType, Product, StockMovement


def test_create_product_success_with_initial_stock(client, test_category, test_supplier, db_session):
    """Cadastrar produto com estoque inicial deve criar automaticamente o registro de movimentação de ENTRADA."""
    payload = {
        "name": "Resistor 10k",
        "sku": "RES-10K-001",
        "cost_price": "0.10",
        "sale_price": "0.50",
        "minimum_stock": 10,
        "initial_stock": 100,
        "category_id": test_category.id,
        "supplier_id": test_supplier.id,
    }

    response = client.post("/product/create", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    product_id = body["data"]["id"]

    # Verifica se a movimentação de ENTRADA foi criada automaticamente
    movement = (
        db_session.query(StockMovement)
        .filter(StockMovement.product_id == product_id)
        .first()
    )
    assert movement is not None
    assert movement.movement_type == MovementType.ENTRADA
    assert movement.quantity == 100


def test_create_product_duplicate_sku_fails(client, test_product, test_category):
    """Cadastrar produto com SKU já existente dispara conflito (409)."""
    payload = {
        "name": "Outro Arduino",
        "sku": test_product.sku,  # Mesmo SKU do fixture
        "cost_price": "30.00",
        "sale_price": "60.00",
        "minimum_stock": 5,
        "initial_stock": 10,
        "category_id": test_category.id,
    }

    response = client.post("/product/create", json=payload)

    assert response.status_code == 409
    assert response.json()["error_code"] == "PRODUCT_SKU_ALREADY_EXISTS"


def test_delete_product_blocked_if_has_stock(client, test_product):
    """Produto com estoque maior que zero não pode sofrer soft delete (409 Conflict)."""
    # test_product começa com 10 unidades
    response = client.delete(f"/product/delete/{test_product.id}")

    assert response.status_code == 409
    body = response.json()
    assert body["error_code"] == "PRODUCT_STILL_HAS_PRODUCTS"


def test_delete_product_success_with_zero_stock(client, test_product, db_session):
    """Produto com estoque zerado pode ser desativado com sucesso."""
    test_product.stock_quantity = 0
    db_session.commit()

    response = client.delete(f"/product/delete/{test_product.id}")

    assert response.status_code == 200
    db_session.refresh(test_product)
    assert test_product.deleted_at is not None


def test_restore_product_blocked_if_category_inactive(client, test_product, test_category, db_session):
    """Restauração deve falhar se a categoria vinculada estiver desativada."""
    # Desativa produto e categoria
    now = datetime.now(timezone.utc)
    test_product.deleted_at = now
    test_category.deleted_at = now
    db_session.commit()

    response = client.patch(f"/product/restore/{test_product.id}")

    assert response.status_code == 409
    assert response.json()["error_code"] == "CATEGORY_NOT_ACTIVED"


def test_modify_product_updates_fields(client, test_product, db_session):
    """Atualização parcial de dados do produto."""
    payload = {
        "name": "Arduino Uno R3 Atualizado",
        "sku": test_product.sku,
        "cost_price": "42.00",
        "sale_price": "80.00",
        "minimum_stock": 4,
    }

    response = client.patch(f"/product/modify?product_id={test_product.id}", json=payload)

    assert response.status_code == 200
    db_session.refresh(test_product)
    assert test_product.name == "Arduino Uno R3 Atualizado"
    assert test_product.sale_price == 80.0
