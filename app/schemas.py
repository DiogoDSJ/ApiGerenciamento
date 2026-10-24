import re
from pydantic import BaseModel, Field, EmailStr, field_validator, model_validator, BaseModel, Field
from app.models import UserRole, MovementType
from decimal import Decimal
from datetime import datetime, timezone
from typing import Generic, TypeVar

T = TypeVar("T")


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

class CategoryResponse(BaseModel):
    id: int
    name: str
    created_at: datetime
    updated_at: datetime | None
    deleted_at: datetime | None

    created_by: int
    updated_by: int | None
    deleted_by: int | None

    class Config:
        from_attributes = True

class CategoryPaginatedResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[CategoryResponse]

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




class StockMovementCreate(BaseModel):
    product_id: int = Field(gt=0, examples=[1], description="Id do produto que sofreu movimentacao")
    movement_type: MovementType = Field(..., examples=["saida"])
    quantity: int = Field(...,ge=0, description="Quantidade a ser movimentada (para ajuste, representa a quantidade física final ou a variação)", examples=[10])
    reason: str | None = Field(default=None, max_length=255, examples=["Avaria na embalagem durante transporte"])

    @model_validator(mode="after")
    def validate_reason_for_critical_movements(self):
        if(self.movement_type in [MovementType.PERDA, MovementType.AJUSTE]):
            if not self.reason or self.reason.strip():
                raise ValueError(f"O campo 'reason' (justificativa) é obrigatório para movimentações do tipo '{self.movement_type.value}'.")
        return self

    @model_validator(mode="after")
    def validate_rules(self):
        if self.movement_type != MovementType.AJUSTE and self.quantity <= 0:
            raise ValueError(
                f"A quantidade para '{self.movement_type.value}' deve ser estritamente maior que zero."
            )
        return self

class StockMovementResponseCreate(BaseModel):
    id: int
    product_id: int
    movement_type: MovementType
    quantity: int
    reason: str | None
    created_at: datetime
    current_product_stock: int  # Saldo do produto após a movimentação]
    created_by: int

    class Config:
        from_attributes = True


class EntitySummary(BaseModel):
    id: int
    name: str
    supplier_id: int | None
    category_id: int

    class Config:
        from_attributes = True


class UserSummary(BaseModel):
    id: int
    username: str

    class Config:
        from_attributes = True

class StockMovementResponseGetSpecific(BaseModel):
    id: int
    product_id: int
    product: EntitySummary
    movement_type: MovementType
    quantity: int
    reason: str | None
    created_at: datetime
    created_by: UserSummary = Field(validation_alias="user")
    class Config:
        from_attributes = True

class StockMovementPaginatedResponseGet(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[StockMovementResponseGetSpecific]

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
        pattern=r"^\d{14}$",
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
    @field_validator("cnpj", mode="before")
    @classmethod
    def normalize_cnpj(cls, v: str) -> str:
        if isinstance(v, str):
            # Remove qualquer caractere que não seja dígito
            v = re.sub(r"\D", "", v)
        return v
    @field_validator("phone", mode="before")
    @classmethod
    def normalize_phone(cls, v: str) -> str:
        if isinstance(v, str):
            # Remove qualquer caractere que não seja dígito
            v = re.sub(r"\D", "", v)
        return v
    class Config:
        from_attributes = True

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str

    created_at: datetime
    updated_at: datetime | None
    deleted_at: datetime | None

    created_by: int | None
    updated_by: int | None
    deleted_by: int | None

    class Config:
        from_attributes = True

class SupplierResponse(BaseModel):
    id: int
    name: str
    cnpj: str
    email: str
    phone: str
    address: str

    created_at: datetime
    updated_at: datetime | None
    deleted_at: datetime | None

    created_by: int
    updated_by: int | None
    deleted_by: int | None

    class Config:
        from_attributes = True

class SupplierPaginatedResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[SupplierResponse]

class UserPaginatedResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[UserResponse]

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
    category_id: int | None = Field(default=None, gt=0, examples=[1])
    supplier_id: int | None = Field(default=None, gt=0, examples=[2])



class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = "Operação realizada com sucesso."
    data: T
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

class RefreshTokenResponse(BaseModel):
    acess_token: str
    token_type: str = "bearer"

