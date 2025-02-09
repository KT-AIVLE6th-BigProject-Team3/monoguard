from fastapi import APIRouter, Form, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse  
from fastapi.templating import Jinja2Templates
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc, func # 목록 최신순 출력을 위한 내림차순 추가
from app.database import SessionLocal
from app.models import User, QnA
from app.routers import auth
from app.utils import hash_password, get_db

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
    db: Session = Depends(get_db)
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
def check_employee_id(employee_id: str, db: Session = Depends(get_db)):
    exists = db.query(User).filter(User.employee_id == employee_id).first()
    return {"exists": bool(exists)}


# 현재 사용자가 읽지 않은 답변 갯수 조회
@router.get("/message_count", response_class=JSONResponse)
def get_user_message_count(
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.get_current_user_from_cookie)
):
    """사용자의 QnA 미확인 답변 개수 및 알림 개수를 반환"""

    if current_user is None:
        raise HTTPException(status_code=401, detail="User not authenticated")

    user_id = current_user['sub']

    # QnA 중 사용자가 읽지 않은 (`alert=True`) 답변 개수 조회
    message_count = db.query(func.count(QnA.id)).filter(QnA.user_id == user_id, QnA.alert == True).scalar()

    # User 테이블에서 `alert` 값 가져오기 (추가적인 전체 알림 개수)
    user = db.query(User).filter(User.employee_id == user_id).first()
    alert_count = user.alert if user else 0

    # `user.message` 값이 변경될 때만 DB 업데이트 수행
    if user and user.message != message_count:
        user.message = message_count
        db.commit()

    return JSONResponse(content={"message_count": message_count, "alert_count": alert_count})