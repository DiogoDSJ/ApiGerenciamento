import os
from dotenv import load_dotenv
from passlib.context import CryptContext

load_dotenv()
secret_key = os.getenv("SECRET_KEY")
algorithm = os.getenv("ALGORITHM")
token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 1))
refresh_token_expire_minutes = int(os.getenv("REFRESH_TOKEN_EXPIRE_MINUTES", 1))


bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
