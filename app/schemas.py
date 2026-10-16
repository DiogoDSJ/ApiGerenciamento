from pydantic import BaseModel


class UserSchema(BaseModel):
    username: str
    password: str
    email: str
    role: str

    class Config:
        from_attributes = True


class CategorySchema(BaseModel):
    name: str
    class Config:
        from_attributes = True

class LoginSchema(BaseModel):
    username: str
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
    name: str
    sku: str
    cost_price: float
    sale_price: float
    minimum_stock: int
    stock_quantity: int
    category_id: int
    supplier_id: int
    class Config:
        from_attributes = True

class SupplierSchema(BaseModel):

    name: str
    cnpj: str
    email: str
    phone: str
    address: str

    class Config:
        from_attributes = True

class RefreshTokenRequest(BaseModel):
    refresh_token: str
