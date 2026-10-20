from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError


app = FastAPI(title="API Estoque")

TRANSLATIONS = {
    "string_too_short": "Deve ter no mínimo {min_length} caracteres.",
    "string_too_long": "Deve ter no máximo {max_length} caracteres.",
    "missing": "Campo obrigatório.",
    "enum": "Opção inválida. Escolha uma das opções válidas.",
    "value_error": "Valor informado é inválido.",
}


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
):
    errors = {}

    for err in exc.errors():
        # Extrai o nome do campo (último elemento de loc, ignorando 'body')
        field_name = err["loc"][-1] if err["loc"] else "geral"
        err_type = err["type"]
        ctx = err.get("ctx", {})

        # Usa mensagem customizada do field_validator se houver
        if err_type == "value_error" and "Value error, " in err["msg"]:
            msg = err["msg"].replace("Value error, ", "")
        elif err_type in TRANSLATIONS:
            msg = TRANSLATIONS[err_type].format(**ctx)
        else:
            msg = err["msg"]

        errors[str(field_name)] = msg

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "message": "Erro de validação nos campos informados.",
            "errors": errors,
        },
    )


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
