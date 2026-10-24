from datetime import datetime, timezone
from app.models import User, UserRole
from app.security import bcrypt_context


def test_admin_cannot_delete_himself(client, test_admin_user):
    """Admin não pode excluir a sua própria conta (deve disparar erro 400)."""
    response = client.delete(f"/users/delete/{test_admin_user.id}")

    assert response.status_code == 400
    body = response.json()
    assert body["success"] is False
    assert (
        body["message"]
        == "Você não pode excluir sua própria conta de administrador."
    )


def test_admin_can_delete_another_user(client, db_session, test_admin_user):
    """Admin pode excluir outros usuários via soft delete."""
    other_user = User(
        username="funcionario_comum",
        email="func@erp.com",
        password=bcrypt_context.hash("senha123"),
        role=UserRole.FUNCIONARIO,
        created_by=test_admin_user.id,
    )
    db_session.add(other_user)
    db_session.commit()

    response = client.delete(f"/users/delete/{other_user.id}")

    assert response.status_code == 200
    db_session.refresh(other_user)
    assert other_user.deleted_at is not None
    assert other_user.deleted_by == test_admin_user.id


def test_admin_cannot_revoke_his_own_role(client, test_admin_user):
    """Admin não pode rebaixar seu próprio papel para funcionário."""
    payload = {"role": "funcionario"}

    response = client.patch(f"/users/update/{test_admin_user.id}", json=payload)

    assert response.status_code == 400
    body = response.json()
    assert body["success"] is False
    assert (
        body["message"]
        == "Você não pode tirar seus direitos de administrador."
    )


def test_update_user_duplicate_username_fails(
    client, db_session, test_admin_user
):
    """Tentativa de trocar o username para um já existente deve retornar 409 Conflict."""
    user2 = User(
        username="usuario_dois",
        email="dois@erp.com",
        password=bcrypt_context.hash("senha123"),
        role=UserRole.FUNCIONARIO,
    )
    db_session.add(user2)
    db_session.commit()

    # Tenta mudar o username do admin para o de user2
    payload = {"username": user2.username}
    response = client.patch(f"/users/update/{test_admin_user.id}", json=payload)

    assert response.status_code == 409
    assert response.json()["error_code"] == "USER_ALREADY_EXISTS"


def test_change_user_password_hashes_new_password(
    client, db_session, test_admin_user
):
    """Alteração de senha deve atualizar o hash no banco."""
    new_raw_password = "nova_senha_forte_456"

    response = client.patch(
        f"/users/{test_admin_user.id}/password?new_password={new_raw_password}"
    )

    assert response.status_code == 200
    assert response.json()["success"] is True

    db_session.refresh(test_admin_user)
    # Garante que a nova senha é válida contra o hash salvo
    assert bcrypt_context.verify(new_raw_password, test_admin_user.password)


def test_restore_user_success(client, db_session, test_admin_user):
    """Restauração de um usuário inativo."""
    inactive_user = User(
        username="usuario_inativo",
        email="inativo@erp.com",
        password=bcrypt_context.hash("senha123"),
        role=UserRole.FUNCIONARIO,
        deleted_at=datetime.now(timezone.utc),
        deleted_by=test_admin_user.id,
    )
    db_session.add(inactive_user)
    db_session.commit()

    response = client.patch(f"/users/restore/{inactive_user.id}")

    assert response.status_code == 200
    db_session.refresh(inactive_user)
    assert inactive_user.deleted_at is None
    assert inactive_user.deleted_by is None
    assert inactive_user.updated_by == test_admin_user.id


def test_get_all_users_filter_by_type(client, db_session, test_admin_user):
    """Valida a listagem de usuários filtrada por perfil."""
    user_func = User(
        username="func_filtro",
        email="filtro@erp.com",
        password=bcrypt_context.hash("senha123"),
        role=UserRole.FUNCIONARIO,
    )
    db_session.add(user_func)
    db_session.commit()

    # Busca apenas ADMINs
    res_admin = client.get("/users/all?user_type=ADMIN")
    assert res_admin.status_code == 200
    items_admin = res_admin.json()["data"]["items"]
    assert all(u["role"] == "admin" for u in items_admin)

    # Busca apenas FUNCIONARIOs
    res_func = client.get("/users/all?user_type=FUNCIONARIO")
    assert res_func.status_code == 200
    items_func = res_func.json()["data"]["items"]
    assert all(u["role"] == "funcionario" for u in items_func)
