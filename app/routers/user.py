from fastapi import APIRouter, Form, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse  
from fastapi.templating import Jinja2Templates
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc # 목록 최신순 출력을 위한 내림차순 추가
from app.database import SessionLocal
from app.models import User
from app.utils import hash_password

router = APIRouter() 
templates = Jinja2Templates(directory="templates")


@router.post("/register", response_class=HTMLResponse)
def register_user(
    request: Request,
    name: str = Form(...),                              # 이름
    employee_id: str = Form(...),                       # 사번
    department: str = Form(...),                        # 부서
    phone: str = Form(...),                             # 전화번호
    email: str = Form(...),                             # 이메일
    password: str = Form(...),                          # 비밀번호
    db: Session = Depends(lambda: SessionLocal())
):

    existing_user = db.query(User).filter(User.employee_id == employee_id).first()
    if existing_user:
        # 예: 400 Bad Request
        raise HTTPException(status_code=400, detail="이미 존재하는 사번입니다.")

    hashed_pw = hash_password(password)
    new_user = User(
        name=name,
        email=email,
        password=hashed_pw, 
        department=department,
        employee_id=employee_id,
        phone=phone,
        admin=False,
        alert=0,
        message=0
    )
    db.add(new_user)
    db.commit()
    
    return "<script>alert('회원가입이 완료되었습니다!'); location.href='/';</script>"

@router.get("/check-id")
def check_employee_id(employee_id: str, db: Session = Depends(lambda: SessionLocal())):
    exists = db.query(User).filter(User.employee_id == employee_id).first()
    return {"exists": bool(exists)}