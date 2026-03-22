# api/routes/auth.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from jose import jwt
import bcrypt
from core.config import settings

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# 這裡建議將 HASHED_PASSWORD 處理邏輯也封裝進來
# 注意：在生產環境，ADMIN_PASSWORD 通常直接存 Hash 好的字串，不建議每次啟動都重新 Hash
HASHED_PASSWORD = bcrypt.hashpw(settings.ADMIN_PASSWORD.encode(), bcrypt.gensalt())

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if form_data.username != settings.ADMIN_USERNAME or \
       not bcrypt.checkpw(form_data.password.encode(), HASHED_PASSWORD):
        raise HTTPException(status_code=401, detail="用戶名或密碼錯誤")
    
    access_token = create_access_token({"sub": form_data.username})
    return {"access_token": access_token, "token_type": "bearer"}