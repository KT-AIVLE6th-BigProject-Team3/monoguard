from fastapi import APIRouter, Form, Depends, HTTPException, Response, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import User
from app.utils import verify_password, create_access_token, verify_access_token

router = APIRouter()

from fastapi.responses import HTMLResponse, RedirectResponse

from fastapi import APIRouter, Form, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import User
from app.utils import verify_password, create_access_token

router = APIRouter()

@router.post("/login")
def login_user(
    response: Response,
    employee_id: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(lambda: SessionLocal())
):
    user = db.query(User).filter(User.employee_id == employee_id).first()
    if not user or not verify_password(password, user.password):
        raise HTTPException(status_code=401, detail="아이디 또는 비밀번호가 잘못되었습니다.")

    # JWT 생성
    access_token = create_access_token(data={"sub": user.employee_id,
                                             "admin":user.admin,
                                             "name":user.name,
                                             "department":user.department,
                                             "alert":user.alert}) 
 
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,       # HTTPS 환경이라면 True 권장
        samesite="strict"   # or 'lax' 
    )
 
    return {"success": True, "message": "로그인 성공"}

def get_current_user_from_cookie(request: Request): 
    token = request.cookies.get("access_token")
    if not token:
        #raise HTTPException(status_code=403, detail="Not authenticated")
        return None

    payload = verify_access_token(token)
    if payload is None:
        #raise HTTPException(status_code=403, detail="Token invalid or expired")
        return None

    return payload

@router.post("/logout")
def logout_user(response: Response):
    response.delete_cookie(
        key="access_token",     # 토큰 쿠키 키
        path="/",               # 루트 경로에서 제거
    )
    return {"success": True, "message": "로그아웃 되었습니다."}