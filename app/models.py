import os
import enum
from sqlalchemy import (
    create_engine,
    Column,
    String,
    Integer,
    Enum,
    Float,
    ForeignKey,
    DateTime,
    func,
    Index,
    CheckConstraint
)
from sqlalchemy.orm import declarative_base, relationship
from dotenv import load_dotenv


load_dotenv()

database_URL = os.getenv("DATABASE_URL")

db = create_engine(database_URL)
Base = declarative_base()

class Category(Base):
    """Represents a product category in the inventory system."""
    __tablename__ = "categories"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    name = Column("name", String, nullable=False)

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


    __table_args__ = (
        Index(
            "ix_categories_active_name_unique",
            "name",
            unique=True,
            postgresql_where=(deleted_at.is_(None)),
        ),
    )


class Product(Base):
    """Represents a product in the inventory system."""
    __tablename__ = "products"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    name = Column("name", String, nullable=False)
    sku = Column("sku", String, nullable=False)
    cost_price = Column("cost_price", Float, nullable=False)
    sale_price = Column("sale_price", Float, nullable=False)
    minimum_stock = Column("minimum_stock", Integer, nullable=False, default=0)
    stock_quantity = Column("stock_quantity", Integer, nullable=False)
    category_id = Column("category_id", Integer, ForeignKey("categories.id"), nullable=False)
    supplier_id = Column("supplier_id", Integer, ForeignKey("suppliers.id"), nullable=True)

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


    __table_args__ = (
        Index(
            "ix_products_active_sku_unique",
            "sku",
            unique=True,
            postgresql_where=(deleted_at.is_(None)),
        ),
        CheckConstraint("stock_quantity >= 0", name="check_product_stock_quantity_positive"),
        CheckConstraint("minimum_stock >= 0", name="check_product_min_stock_positive"),
        CheckConstraint("cost_price >= 0", name="check_product_cost_price_positive"),
        CheckConstraint("sale_price >= 0", name="check_product_sale_price_positive"),
    )

class Supplier(Base):
    """Represents a supplier in the inventory system."""
    __tablename__ = "suppliers"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    name = Column("name", String, nullable=False)
    cnpj = Column("cnpj", String, nullable=False)
    email = Column("email", String, nullable=False)
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

    __table_args__ = (
        # CNPJ único apenas entre ativos:
        Index(
            "ix_suppliers_active_cnpj_unique",
            "cnpj",
            unique=True,
            postgresql_where=(deleted_at.is_(None)),
        ),
        # Email de contato único apenas entre ativos:
        Index(
            "ix_suppliers_active_email_unique",
            "email",
            unique=True,
            postgresql_where=(deleted_at.is_(None)),
        ),
    )




class MovementType(str, enum.Enum):
    """
    Enum representing the type of stock movement.
    """
    ENTRADA = "entrada"
    SAIDA = "saida"
    PERDA = "perda"
    AJUSTE = "ajuste"





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
    reason = Column(String(255), nullable=True)

    created_by = Column("created_by", Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False)


    product = relationship("Product", back_populates="stock_movements")
    user = relationship("User", backref="stock_movements")

    __table_args__ = (
        # Garante no PostgreSQL que a quantidade movimentada seja sempre positiva e maior que zero
        CheckConstraint("quantity > 0", name="check_stock_movement_quantity_strictly_positive"),
    )


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
    username = Column(String, nullable=False)
    email = Column(String, nullable=False)
    password = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.FUNCIONARIO)

    created_by = Column("created_by", Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False)

    updated_by = Column("updated_by", Integer, ForeignKey("users.id"), nullable=True)
    updated_at = Column("updated_at", DateTime(timezone=True), onupdate=func.now(), nullable=True)

    deleted_by = Column("deleted_by", Integer, ForeignKey("users.id"), nullable=True)
    deleted_at = Column("deleted_at", DateTime(timezone=True), nullable=True)

    __table_args__ = (
        # usuario único apenas entre ativos:
        Index(
            "ix_users_active_username_unique",
            "username",
            unique=True,
            postgresql_where=(deleted_at.is_(None)),
        ),
        # Email de contato único apenas entre ativos:
        Index(
            "ix_users_active_email_unique",
            "email",
            unique=True,
            postgresql_where=(deleted_at.is_(None)),
        ),
    )
