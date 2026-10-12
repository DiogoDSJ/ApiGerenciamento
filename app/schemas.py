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
    created_by: int

    class Config:
        from_attributes = True

class LoginSchema(BaseModel):
    username: str
    password: str

    class Config:
        from_attributes = True

class TokenSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

    class Config:
        from_attributes = True


class StockMovementSchema(BaseModel):
    product_id: int
    quantity: int
    movement_type: str  # "entrada" ou "saida"
    created_by: int

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
    created_by: int

    class Config:
        from_attributes = True
