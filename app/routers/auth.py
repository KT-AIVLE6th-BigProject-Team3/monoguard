from fastapi import APIRouter, Form, Depends, HTTPException, Response, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import User
from app.utils import verify_password, create_access_token, verify_access_token, hash_password, get_db

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
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.employee_id == employee_id).first()
    if not user or not verify_password(password, user.password):
        raise HTTPException(status_code=401, detail="아이디 또는 비밀번호가 잘못되었습니다.")

    # JWT 생성
    access_token = create_access_token(data={"sub": user.employee_id,
                                             "admin":user.admin,
                                             "name":user.name,
                                             "department":user.department,
                                             "alert":user.alert,
                                             "message":user.message}) 
 
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

# ID 찾기
@router.post("/find_id")
def find_user_id(email: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="해당 이메일을 가진 사용자가 없습니다.")
    
    return {"message": "사번 찾기 성공", "employee_id": user.employee_id}

# PW 찾기(변경) 
@router.post("/reset_password")
def reset_password(
    email: str = Form(...),             # 이메일 확인
    employee_id: str = Form(...),       # 사번 확인
    new_password: str = Form(...),      # 변경할 새 비밀번호
    confirm_password: str = Form(...),  # 비밀번호 확인
    db: Session = Depends(get_db)
):
    if new_password != confirm_password:
        raise HTTPException(status_code=400, detail="비밀번호가 일치하지 않습니다.")

    user = db.query(User).filter(User.email == email, User.employee_id == employee_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="입력한 정보와 일치하는 회원이 없습니다.")

    hashed_pw = hash_password(new_password)
    user.password = hashed_pw
    db.commit()

    return {"message": "비밀번호 변경 완료"}

