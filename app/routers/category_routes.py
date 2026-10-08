from fastapi import APIRouter

category_router = APIRouter(prefix="/category", tags=["category"])

@category_router.get("/list")
async def return_all_category():
    """Retorna todas as categorias disponíveis no sistema."""
    return {"message": "Lista de todas as categorias disponíveis."}