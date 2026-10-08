import enum
from datetime import datetime, timezone
from sqlalchemy import (
    create_engine,
    Column,
    String,
    Integer,
    Enum,
    Float,
    ForeignKey,
    DateTime,
    func
)
from sqlalchemy.orm import declarative_base, relationship
from dotenv import load_dotenv
import os


load_dotenv()

database_URL = os.getenv("DATABASE_URL")

db = create_engine(database_URL)
Base = declarative_base()

class Category(Base):
    """Represents a product category in the inventory system."""
    __tablename__ = "categories"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    name = Column("name", String, nullable=False, unique=True)

    products = relationship("Product", back_populates="category")


    def __init__(self, name: str):
        self.name = name





class Product(Base):
    """Represents a product in the inventory system."""
    __tablename__ = "products"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    name = Column("name", String, nullable=False, unique=False)
    sku = Column("sku", String, nullable=False, unique=True)
    cost_price = Column("cost_price", Float, nullable=False)
    sale_price = Column("sale_price", Float, nullable=False)
    minimum_stock = Column("minimum_stock", Integer, nullable=False, default=0)
    stock_quantity = Column("stock_quantity", Integer, nullable=False)
    data_created = Column("data_created", DateTime(timezone=True), server_default=func.now(), nullable=False)
    category_id = Column("category_id", Integer, ForeignKey("categories.id"), nullable=False)
    supplier_id = Column("supplier_id", Integer, ForeignKey("suppliers.id"), nullable=False)

    category = relationship("Category", back_populates="products")
    supplier = relationship("Supplier", back_populates="products")
    stock_movements = relationship("StockMovement", back_populates="product")

    def __init__(self, name: str, sku: str, cost_price: float, sale_price: float, stock_quantity: int, category_id: int, supplier_id: int, data_created=None, minimum_stock: int = 0):
        self.name = name
        self.sku = sku
        self.cost_price = cost_price
        self.sale_price = sale_price
        self.stock_quantity = stock_quantity
        self.minimum_stock = minimum_stock
        self.data_created = data_created if data_created is not None else datetime.now(timezone.utc)
        self.category_id = category_id
        self.supplier_id = supplier_id





class Supplier(Base):
    """Represents a supplier in the inventory system."""
    __tablename__ = "suppliers"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    name = Column("name", String, nullable=False)
    cnpj = Column("cnpj", String, nullable=False, unique=True)
    email = Column("email", String, nullable=False, unique=True)
    phone = Column("phone", String, nullable=False)
    address = Column("address", String, nullable=False)

    products = relationship("Product", back_populates="supplier")

    def __init__(self, name: str, cnpj: str, email: str, phone: str, address: str):
        self.name = name
        self.cnpj = cnpj
        self.email = email
        self.phone = phone
        self.address = address





class MovementType(str, enum.Enum):
    """
    Enum representing the type of stock movement.
    """
    ENTRADA = "entrada"
    SAIDA = "saida"





class StockMovement(Base):
    """
    Represents a stock movement in the inventory system.
    """
    __tablename__ = "stock_movements"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    product_id = Column("product_id", Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column("quantity", Integer, nullable=False)
    movement_type = Column("movement_type",
    Enum(MovementType, values_callable=lambda obj: [member.value for member in obj], name="movement_type_enum"),
    nullable=False)  # 'entrada' ou 'saida'
    data_created = Column("data_created", DateTime(timezone=True), server_default=func.now(), nullable=False)

    created_by = Column("created_by", Integer, ForeignKey("users.id"), nullable=False)

    product = relationship("Product", back_populates="stock_movements")

    def __init__(self, product_id: int, quantity: int, movement_type: MovementType, created_by: int, data_created=None):
        self.product_id = product_id
        self.quantity = quantity
        self.movement_type = movement_type
        self.created_by = created_by
        self.data_created = data_created if data_created is not None else datetime.now(timezone.utc)


class UserRole(str, enum.Enum):
    """
    Enum representing the role of a user in the system.
    """
    ADMIN = "admin"
    FUNCIONARIO = "funcionario"

class User(Base):
    """
    Represents the user who will acess the system info, which can be only read view or write view. And that employee can be a manager or a regular employee. The user will have a username, email and password to access the system.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, nullable=False, unique=True)
    email = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.FUNCIONARIO)
    data_created = Column("data_created", DateTime(timezone=True), server_default=func.now(), nullable=False)


    category = relationship("Category", back_populates="user")
    stock_movements = relationship("StockMovement", back_populates="user")
