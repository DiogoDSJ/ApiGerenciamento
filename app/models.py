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

    #Auditoria de criacao
    created_by = Column("created_by", Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False)

    #auditoria de edicao
    updated_by = Column("updated_by", Integer, ForeignKey("users.id"), nullable=True)
    updated_at = Column("updated_at", DateTime(timezone=True), onupdate=func.now(), nullable=True)

    #auditoria de exclusao
    deleted_by = Column("deleted_by", Integer, ForeignKey("users.id"), nullable=True)
    deleted_at = Column("deleted_at", DateTime(timezone=True), nullable=True)

    products = relationship("Product", back_populates="category")

    created_by_user = relationship("User", foreign_keys=[created_by])
    updated_by_user = relationship("User", foreign_keys=[updated_by])
    deleted_by_user = relationship("User", foreign_keys=[deleted_by])




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
    category_id = Column("category_id", Integer, ForeignKey("categories.id"), nullable=False)
    supplier_id = Column("supplier_id", Integer, ForeignKey("suppliers.id"), nullable=False)

    category = relationship("Category", back_populates="products")
    supplier = relationship("Supplier", back_populates="products")
    stock_movements = relationship("StockMovement", back_populates="product")

    created_by = Column("created_by", Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False)

    updated_by = Column("updated_by", Integer, ForeignKey("users.id"), nullable=True)
    updated_at = Column("updated_at", DateTime(timezone=True), onupdate=func.now(), nullable=True)

    deleted_by = Column("deleted_by", Integer, ForeignKey("users.id"), nullable=True)
    deleted_at = Column("deleted_at", DateTime(timezone=True), nullable=True)

    created_by_user = relationship("User", foreign_keys=[created_by])
    updated_by_user = relationship("User", foreign_keys=[updated_by])
    deleted_by_user = relationship("User", foreign_keys=[deleted_by])


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


    created_by = Column("created_by", Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False)

    updated_by = Column("updated_by", Integer, ForeignKey("users.id"), nullable=True)
    updated_at = Column("updated_at", DateTime(timezone=True), onupdate=func.now(), nullable=True)

    deleted_by = Column("deleted_by", Integer, ForeignKey("users.id"), nullable=True)
    deleted_at = Column("deleted_at", DateTime(timezone=True), nullable=True)

    created_by_user = relationship("User", foreign_keys=[created_by])
    updated_by_user = relationship("User", foreign_keys=[updated_by])
    deleted_by_user = relationship("User", foreign_keys=[deleted_by])





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


    created_by = Column("created_by", Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False)


    product = relationship("Product", back_populates="stock_movements")


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

    created_by = Column("created_by", Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False)

    updated_by = Column("updated_by", Integer, ForeignKey("users.id"), nullable=True)
    updated_at = Column("updated_at", DateTime(timezone=True), onupdate=func.now(), nullable=True)

    deleted_by = Column("deleted_by", Integer, ForeignKey("users.id"), nullable=True)
    deleted_at = Column("deleted_at", DateTime(timezone=True), nullable=True)
