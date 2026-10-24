from datetime import datetime, timezone
from app.models import Supplier


def test_create_supplier_success(client, db_session):
    """Criação bem-sucedida de fornecedor com formatação de CNPJ e telefone."""
    payload = {
        "name": "Componentes Brasil Ltda",
        "cnpj": "12.345.678/0001-95",
        "email": "contato@compbrasil.com",
        "phone": "(75) 99888-7766",
        "address": "Av. Maria Quitéria, 500",
    }
    response = client.post("/supplier/create", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    # O validador do Pydantic normaliza apenas para números
    assert body["data"]["cnpj"] == "12345678000195"
    assert body["data"]["phone"] == "75998887766"


def test_create_supplier_duplicate_cnpj_fails(client, test_supplier):
    """CNPJ duplicado deve disparar SupplierCnpjConflictException (409)."""
    payload = {
        "name": "Outro Fornecedor",
        "cnpj": test_supplier.cnpj,  # Mesmo CNPJ do fixture
        "email": "outro@teste.com",
        "phone": "75911112222",
        "address": "Rua B, 200",
    }
    response = client.post("/supplier/create", json=payload)

    assert response.status_code == 409
    body = response.json()
    assert body["error_code"] == "SUPPLIER_CNPJ_ALREADY_EXISTS"


def test_delete_supplier_blocked_with_active_products(client, test_supplier, test_product):
    """Fornecedor com produto ativo associado não pode ser excluído (409)."""
    response = client.delete(f"/supplier/delete/{test_supplier.id}")

    assert response.status_code == 409
    body = response.json()
    assert body["error_code"] == "SUPPLIER_STILL_HAS_PRODUCTS"


def test_delete_supplier_success_when_no_products(client, db_session, test_admin_user):
    """Soft delete permitido quando não há produtos ativos vinculados."""
    supp = Supplier(
        name="Fornecedor Sem Produtos",
        cnpj="99888777000166",
        email="semprodutos@teste.com",
        phone="75922223333",
        address="Rua C, 300",
        created_by=test_admin_user.id,
    )
    db_session.add(supp)
    db_session.commit()

    response = client.delete(f"/supplier/delete/{supp.id}")

    assert response.status_code == 200
    db_session.refresh(supp)
    assert supp.deleted_at is not None
    assert supp.deleted_by == test_admin_user.id


def test_restore_supplier_success(client, db_session, test_admin_user):
    """Restauração de fornecedor inativo."""
    supp = Supplier(
        name="Fornecedor Inativo",
        cnpj="55444333000122",
        email="inativo@teste.com",
        phone="75933334444",
        address="Rua D, 400",
        created_by=test_admin_user.id,
        deleted_by=test_admin_user.id,
        deleted_at=datetime.now(timezone.utc),
    )
    db_session.add(supp)
    db_session.commit()

    response = client.patch(f"/supplier/restore/{supp.id}")

    assert response.status_code == 200
    db_session.refresh(supp)
    assert supp.deleted_at is None


def test_search_supplier_with_filters(client, test_supplier):
    """Busca com filtro por termo textual (nome, cnpj, email ou telefone)."""
    response = client.get(f"/supplier?search={test_supplier.name[:4]}")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["total"] >= 1
