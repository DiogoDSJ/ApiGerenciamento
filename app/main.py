from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from app.error_handlers import (
    app_exception_handler,
    validation_exception_handler,
)
from app.exceptions import AppException

app = FastAPI(title="API Estoque")

TRANSLATIONS = {
    "string_too_short": "Deve ter no mínimo {min_length} caracteres.",
    "string_too_long": "Deve ter no máximo {max_length} caracteres.",
    "missing": "Campo obrigatório.",
    "enum": "Opção inválida. Escolha uma das opções válidas.",
    "value_error": "Valor informado é inválido.",
}


app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)


from app.routers.category_routes import category_router
from app.routers.auth_routes import auth_router
from app.routers.supplier_routes import supplier_router
from app.routers.user_routes import user_router
from app.routers.product_routes import product_router
from app.routers.stock_movements_routes import stock_movements_router


app.include_router(category_router)
app.include_router(auth_router)
app.include_router(supplier_router)
app.include_router(user_router)
app.include_router(product_router)
app.include_router(stock_movements_router)

@app.get("/")
def read_root():
    return {"Hello!!!": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}
