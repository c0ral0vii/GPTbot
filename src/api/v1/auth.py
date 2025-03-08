import uuid
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from src.api.models.models import UserLoginSchema
from src.config.config import settings
from authx import AuthX, AuthXConfig

router = APIRouter()
config = AuthXConfig()
config.JWT_SECRET_KEY = settings.ADMIN_TOKEN
config.JWT_ACCESS_COOKIE_NAME = "JWT_TOKEN"
config.JWT_TOKEN_LOCATION = ["cookies"]

security = AuthX(config=config)


@router.post("/login")
async def login(creds: UserLoginSchema):
    if creds.username == settings.ADMIN_USER and creds.password == settings.ADMIN_PASS:
        token = security.create_access_token(uid=str(uuid.uuid4()))

        print("✅ Устанавливаем куку my_access_token")
        data = JSONResponse({"access_token": token})
        data.set_cookie(key=config.JWT_ACCESS_COOKIE_NAME, value=token)
        return data

    raise HTTPException(status_code=401, detail="Invalid username or password")
