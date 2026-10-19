from pydantic import BaseModel, Field, EmailStr
from app.models import UserRole
from decimal import Decimal
from datetime import datetime

class UserSchema(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=50,
        pattern=r"^\S+$",  # Impede qualquer espaço em branco (inclusive string vazia "")
        description="Nome de usuário sem espaços"
    )
    password: str
    email: EmailStr
    role: UserRole

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    username: str | None = Field(
        default = None,
        min_length=3,
        max_length=50,
        pattern=r"^\S+$",  # Impede qualquer espaço em branco (inclusive string vazia "")
        description="Nome de usuário sem espaços"
    )
    email: EmailStr | None = None
    role: UserRole | None = None

class CategorySchema(BaseModel):
    name: str = Field(
        min_length=2, max_length=150, description="Nome da categoria"
    )
    class Config:
        from_attributes = True

class LoginSchema(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=50,
        pattern=r"^\S+$",  # Impede qualquer espaço em branco (inclusive string vazia "")
        description="Nome de usuário sem espaços"
    )
    password: str


class TokenSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class StockMovementSchema(BaseModel):
    product_id: int
    quantity: int
    movement_type: str  # "entrada" ou "saida"
    class Config:
        from_attributes = True

class ProductSchema(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=120,
        description="Nome comercial do produto",
        examples=["Caderno Universitário 10 Matérias"],
    )
    sku: str = Field(
        min_length=3,
        max_length=30,
        pattern=r"^[A-Z0-9-]+$",
        description="Código identificador SKU (apenas maiúsculas, números e hífens)",
        examples=["PAP-CAD-001", "ELETR-CABO-02"],
    )
    cost_price: Decimal = Field(
        gt=0,  # Maior que zero estrito
        max_digits=10,  # Até 99.999.999,99
        decimal_places=2,
        description="Preço final de venda",
        examples=[19.90],
    )
    sale_price: Decimal = Field(
        gt=0,  # Maior que zero estrito
        max_digits=10,  # Até 99.999.999,99
        decimal_places=2,
        description="Preço final de venda",
        examples=[19.90],
    )
    minimum_stock: int = Field(
        default=0,
        ge=0,
        le=100_000,
        description="Ponto de pedido / estoque mínimo de segurança",
        examples=[10],
    )
    stock_quantity: int = Field(
        default=0,
        ge=0,
        le=1_000_000,
        description="Saldo atual de unidades em estoque (não-negativo)",
        examples=[50],
    )
    category_id: int
    supplier_id: int | None = Field(default=None, gt=0, examples=[2])
    class Config:
        from_attributes = True

class ProductCreate(BaseModel):
    name: str = Field(
        ...,
        min_length=2,
        max_length=150,
        examples=["Farinha de Trigo Especial 1kg"],
    )
    sku: str = Field(..., min_length=2, max_length=50, examples=["FAR-TRI-001"])
    sale_price: Decimal = Field(..., gt=0, decimal_places=2, examples=[8.50])
    cost_price: Decimal | None = Field(
        default=None, ge=0, decimal_places=2, examples=[5.20]
    )
    minimum_stock: int = Field(default=0, ge=0, examples=[10])
    initial_stock: int = Field(default=0, ge=0, examples=[50])

    category_id: int = Field(..., gt=0, examples=[1])
    supplier_id: int | None = Field(default=None, gt=0, examples=[2])

class SupplierSchema(BaseModel):

    name: str = Field(
        min_length=2, max_length=150, description="Nome da fornecedor"
    )
    cnpj: str = Field(
        ...,
        pattern=r"^\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}$|^\d{14}$",
        description="CNPJ da empresa (com ou sem máscara)",
        examples=["12.345.678/0001-90", "12345678000190"],
    )
    email: EmailStr
    phone: str | None = Field(
        default=None,
        pattern=r"^\(?\d{2}\)?\s?9?\d{4}-?\d{4}$",
        description="Telefone com DDD",
        examples=["75999998888", "(75) 3221-4040"],
    )
    address: str | None = Field(
        default = None,
        min_length=3,
        max_length=120,
        description="Endereco do fornecedor"
    )

    class Config:
        from_attributes = True

class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ProductResponse(BaseModel):
    id: int
    name: str
    sku: str
    sale_price: Decimal
    cost_price: Decimal | None
    stock_quantity: int
    minimum_stock: int
    category_id: int
    supplier_id: int | None
    created_at: datetime
    updated_at: datetime | None
    deleted_at: datetime | None

    created_by: int
    updated_by: int | None
    deleted_by: int | None

    class Config:
        from_attributes = True


class ProductPaginatedResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[ProductResponse]

class ProductUpdate(BaseModel):
    name: str = Field(
        ...,
        min_length=2,
        max_length=150,
        examples=["Farinha de Trigo Especial 1kg"],
    )
    sku: str = Field(..., min_length=2, max_length=50, examples=["FAR-TRI-001"])
    cost_price: Decimal | None = Field(
            default=None,
            gt=0,  # Maior que zero estrito
            max_digits=10,  # Até 99.999.999,99
            decimal_places=2,
            description="Preço final de venda",
            examples=[19.90],
        )
    sale_price: Decimal = Field(
        gt=0,  # Maior que zero estrito
        max_digits=10,  # Até 99.999.999,99
        decimal_places=2,
        description="Preço final de venda",
        examples=[19.90],
    )
    minimum_stock: int = Field(
        default=0,
        ge=0,
        le=100_000,
        description="Ponto de pedido / estoque mínimo de segurança",
        examples=[10],
    )
    category_id: int = Field(..., gt=0, examples=[1])
    supplier_id: int | None = Field(default=None, gt=0, examples=[2])
