import os
from fastapi import FastAPI
from passlib.context import CryptContext
from dotenv import load_dotenv


load_dotenv()
secret_key = os.getenv("SECRET_KEY")
algorithm = os.getenv("ALGORITHM")
token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 1))
refresh_token_expire_minutes = int(os.getenv("REFRESH_TOKEN_EXPIRE_MINUTES", 1))
app = FastAPI()

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

from app.routers.category_routes import category_router
from app.routers.auth_routes import auth_router

app.include_router(category_router)
app.include_router(auth_router)

@app.get("/")
def read_root():
    return {"Hello!!!": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}
