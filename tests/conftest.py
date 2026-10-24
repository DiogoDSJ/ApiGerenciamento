import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.dependencies import get_current_user, get_db_session, require_admin
from app.main import app
from app.models import Base, Category, Product, Supplier, User, UserRole
from app.security import bcrypt_context

# Banco SQLite em memória com conexão única compartilhada
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine
)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Cria todas as tabelas no início e limpa ao final."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    """Fornece uma sessão isolada para cada teste."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def test_admin_user(db_session):
    """Cria um usuário administrador no banco para auditoria."""
    user = User(
        username="admin_test",
        email="admin@erp.com",
        password=bcrypt_context.hash(
            "admin123"
        ),
        role=UserRole.ADMIN,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_category(db_session, test_admin_user):
    """Cria uma categoria ativa."""
    category = Category(
        name="Eletrônicos",
        created_by=test_admin_user.id,
    )
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)
    return category


@pytest.fixture
def test_supplier(db_session, test_admin_user):
    """Cria um fornecedor ativo."""
    supplier = Supplier(
        name="Tech Distribuidora",
        cnpj="11222333000144",
        email="contato@techdist.com",
        phone="75988887777",
        address="Rua A, 123",
        created_by=test_admin_user.id,
    )
    db_session.add(supplier)
    db_session.commit()
    db_session.refresh(supplier)
    return supplier


@pytest.fixture
def test_product(db_session, test_admin_user, test_category, test_supplier):
    """Cria um produto ativo com estoque inicial de 10 unidades."""
    product = Product(
        name="Arduino Uno",
        sku="ARD-UNO-R3",
        cost_price=40.0,
        sale_price=75.0,
        minimum_stock=2,
        stock_quantity=10,
        category_id=test_category.id,
        supplier_id=test_supplier.id,
        created_by=test_admin_user.id,
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product


@pytest.fixture
def client(db_session, test_admin_user):
    """TestClient configurado com override das dependências de sessão e usuário."""

    def override_get_db_session():
        yield db_session

    def override_get_current_user():
        return test_admin_user

    def override_require_admin():
        return test_admin_user

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[require_admin] = override_require_admin

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
