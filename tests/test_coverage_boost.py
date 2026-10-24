import pytest
from datetime import datetime, timezone, timedelta
from jose import jwt
from fastapi.testclient import TestClient

from app.main import app
from app.models import User, UserRole, Category, Product, Supplier
from app.security import secret_key, algorithm, bcrypt_context
from app.exceptions import InvalidCredentialsException, InsufficientPermision
from app.dependencies import get_current_user, require_admin, get_db_session


# --- 1. Testando app/dependencies.py diretamente ---

def test_dependencies_real_get_current_user_and_require_admin(db_session):
    """Testa a lógica real de decodificação JWT do get_current_user usando o banco do teste."""
    # 1. Cria usuário no banco do teste
    user = User(
        username="user_real_jwt",
        email="realjwt@test.com",
        password=bcrypt_context.hash("pass123"),
        role=UserRole.ADMIN,
    )
    db_session.add(user)
    db_session.commit()

    # 2. Gera token JWT válido
    expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    token = jwt.encode(
        {"sub": user.username, "exp": expire, "type": "access"},
        secret_key,
        algorithm=algorithm,
    )

    # 3. Mantém apenas a sessão do banco mockada (para apontar pro SQLite do teste),
    # mas NÃO faz override de get_current_user nem de require_admin!
    app.dependency_overrides[get_db_session] = lambda: db_session

    try:
        with TestClient(app) as client:
            # Requisição com token legítimo (deve passar e retornar 200)
            res = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
            assert res.status_code == 200
            assert res.json()["data"]["username"] == user.username

            # Token inválido/corrompido (deve disparar 401 via InvalidCredentialsException)
            res_invalid = client.get(
                "/auth/me", headers={"Authorization": "Bearer token_falsificado"}
            )
            assert res_invalid.status_code == 401

            # Sem token / sem header de autorização (deve barrar com 401/403 do HTTPBearer)
            res_no_auth = client.get("/auth/me")
            assert res_no_auth.status_code in [401, 403]
    finally:
        app.dependency_overrides.clear()


def test_require_admin_raises_for_regular_employee(db_session):
    """Garante que a dependência real require_admin barra role FUNCIONARIO."""
    user = User(
        username="func_sem_privilegio",
        email="func_sem_priv@test.com",
        password=bcrypt_context.hash("pass123"),
        role=UserRole.FUNCIONARIO,
    )
    with pytest.raises(InsufficientPermision):
        require_admin(current_user=user)


# --- 2. Testando app/error_handlers.py (linhas 28-39) ---

def test_validation_error_handler_formats_pydantic_errors(client):
    """Envia payload com tipo e tamanho incorretos para acionar validation_exception_handler."""
    payload = {
        "name": "A",  # Menor que min_length=2
        "sku": "invalido com espacos",  # Não atende ao regex
        "sale_price": -10,  # Menor ou igual a zero
        "category_id": "nao_e_numero",  # Tipo incorreto
    }
    response = client.post("/product/create", json=payload)
    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert body["error_code"] == "VALIDATION_ERROR"
    assert "validation_errors" in body["details"]
    assert len(body["details"]["validation_errors"]) > 0


# --- 3. Cobrindo app/routers/category_routes.py ---

def test_category_search_filter_inactive_and_update(client, db_session, test_admin_user):
    """Cobre as queries de listagem inativa e atualização de categoria."""
    cat = Category(
        name="Categoria Antiga",
        created_by=test_admin_user.id,
        deleted_by=test_admin_user.id,
        deleted_at=datetime.now(timezone.utc),
    )
    db_session.add(cat)
    db_session.commit()

    # Busca com filtro inativo
    res_search = client.get("/category?status_filter=inactive")
    assert res_search.status_code == 200
    assert res_search.json()["data"]["total"] >= 1

    # Atualiza categoria ativa
    cat_active = Category(name="Categoria Editavel", created_by=test_admin_user.id)
    db_session.add(cat_active)
    db_session.commit()

    res_update = client.patch(f"/category/update/{cat_active.id}", json={"name": "Categoria Renomeada"})
    assert res_update.status_code == 200
    assert res_update.json()["data"]["name"] == "Categoria Renomeada"


# --- 4. Cobrindo app/routers/supplier_routes.py ---

def test_supplier_update_and_search_inactive(client, db_session, test_supplier):
    """Cobre rotas de atualização e listagem de inativos de fornecedor."""
    # Listagem de fornecedores inativos
    res = client.get("/supplier?status_filter=inactive")
    assert res.status_code == 200

    # Atualização de campos do fornecedor
    payload_update = {
        "name": "Tech Distribuidora Modificada",
        "cnpj": test_supplier.cnpj,
        "email": "novo_email@techdist.com",
        "phone": test_supplier.phone,
        "address": "Novo Endereço 500",
    }
    res_update = client.patch(f"/supplier/update/{test_supplier.id}", json=payload_update)
    assert res_update.status_code == 200
    assert res_update.json()["data"]["email"] == "novo_email@techdist.com"


# --- 5. Cobrindo app/routers/product_routes.py ---

def test_product_search_filters_and_missing_branches(client, test_product, test_category, test_supplier):
    """Cobre os filtros combinados de busca de produtos."""
    # Filtro por fornecedor, categoria, low_stock e status_filter
    url = (
        f"/product?search={test_product.name[:3]}"
        f"&category_id={test_category.id}"
        f"&supplier_id={test_supplier.id}"
        f"&low_stock=false"
        f"&status_filter=active"
    )
    res = client.get(url)
    assert res.status_code == 200
    assert res.json()["data"]["total"] >= 1
