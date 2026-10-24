from app.models import Category, Product


def test_create_category_success(client, db_session):
    """Criação bem-sucedida de categoria."""
    payload = {"name": "Ferramentas"}
    response = client.post("/category/create", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["name"] == "Ferramentas"
    assert body["data"]["id"] is not None


def test_create_category_duplicate_name_fails(client, test_category):
    """Tentativa de cadastrar categoria com nome idêntico deve retornar 409."""
    payload = {"name": test_category.name}
    response = client.post("/category/create", json=payload)

    assert response.status_code == 409
    body = response.json()
    assert body["error_code"] == "CATEGORY_ALREADY_EXISTS"


def test_delete_category_success_when_no_products(client, db_session, test_admin_user):
    """Exclusão lógica (soft delete) permitida quando não há produtos ativos vinculados."""
    cat = Category(name="Mobiliário", created_by=test_admin_user.id)
    db_session.add(cat)
    db_session.commit()

    response = client.delete(f"/category/delete/{cat.id}")

    assert response.status_code == 200
    db_session.refresh(cat)
    assert cat.deleted_at is not None
    assert cat.deleted_by == test_admin_user.id


def test_delete_category_blocked_with_active_products(client, test_category, test_product):
    """Categoria com produtos ativos vinculados não pode ser excluída (409 Conflict)."""
    response = client.delete(f"/category/delete/{test_category.id}")

    assert response.status_code == 409
    body = response.json()
    assert body["error_code"] == "CATEGORY_STILL_HAS_PRODUCTS"


def test_restore_category_success(client, db_session, test_admin_user):
    """Restauração de categoria inativa."""
    cat = Category(
        name="Cabos e Fios",
        created_by=test_admin_user.id,
        deleted_by=test_admin_user.id,
    )
    db_session.add(cat)
    db_session.commit()

    # Aplica soft delete manual
    from datetime import datetime, timezone
    cat.deleted_at = datetime.now(timezone.utc)
    db_session.commit()

    response = client.patch(f"/category/restore/{cat.id}")

    assert response.status_code == 200
    db_session.refresh(cat)
    assert cat.deleted_at is None


def test_get_category_not_found(client):
    """Busca por ID inexistente dispara 404."""
    response = client.get("/category/999999")
    assert response.status_code == 404
    assert response.json()["error_code"] == "CATEGORY_NOT_FOUND"
