from fastapi import APIRouter, Form, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import desc # 목록 최신순 출력을 위한 내림차순 추가
from app.database import SessionLocal
from app.models import User
from app.routers import user, auth

router = APIRouter() 
templates = Jinja2Templates(directory="templates")

@router.get("/userlist", response_class=HTMLResponse)
def list_user(
    request: Request,
    current_user: dict = Depends(auth.get_current_user_from_cookie),
    page: int = 0,
    limit: int = 10,
    db: Session = Depends(lambda: SessionLocal())
):
    users = db.query(User).order_by(desc(User.created_at)).offset(page * limit).limit(limit).all()
    user_list = []
    for user in users:
        user_list.append({
            "id": user.id,
            "name": user.name,
            "employee_id": user.employee_id,
            "department": user.department,
            "phone": user.phone,
            "email": user.email,
            "admin": user.admin,
            "created_at": user.created_at,
        })
    
    if current_user is None:
        return RedirectResponse(url="/error?code=invalid_token", status_code=303)
    elif current_user['admin'] is False:
        return RedirectResponse(url="/error?code=invalid_admin", status_code=303)

    return templates.TemplateResponse(
        "admin/user_management.html",
        {
            "request": request,
            "userList": user_list,
            "current_page": page,
            "limit": limit,
            "user" : current_user
        }
    )
        
    
@router.delete("/delete_user/{user_id}")
def delete_user(
    user_id: int,
    current_user: dict = Depends(auth.get_current_user_from_cookie),
    db: Session = Depends(lambda: SessionLocal())
):
    if current_user is None or not current_user.get("admin", False):
        return RedirectResponse(url="/error?code=invalid_admin", status_code=303)

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="해당 유저를 찾을 수 없습니다.")

    db.delete(user)
    db.commit()

    return JSONResponse(content={"message": f"{user.name} 사용자를 삭제 완료하였습니다.", "user_id": user_id}, status_code=200)


@router.get("/edit_user/{user_id}", response_class=HTMLResponse)
def edit_user_form(
    request: Request,
    user_id: int,
    current_user: dict = Depends(auth.get_current_user_from_cookie),
    db: Session = Depends(lambda: SessionLocal())
):
    if current_user is None or not current_user.get("admin", False):
        return RedirectResponse(url="/error?code=invalid_admin", status_code=303)

    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="해당 유저를 찾을 수 없습니다.")

    return templates.TemplateResponse("/admin/admin_edituser.html", {
        "request": request,
        "user": current_user,     # 현재 로그인한 관리자
        "target_user": target_user  # 수정 대상 유저 정보
    })

@router.post("/edit_user/{user_id}", response_class=HTMLResponse)
def update_user(
    user_id: int,
    name: str = Form(...),
    department: str = Form(...),
    phone: str = Form(None),
    email: str = Form(...),
    current_user: dict = Depends(auth.get_current_user_from_cookie),
    db: Session = Depends(lambda: SessionLocal())
):
    # 1. 관리자 권한 체크
    if current_user is None or not current_user.get("admin", False):
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")

    # 2. 대상 유저 조회
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="해당 유저를 찾을 수 없습니다.")

    # 3. 수정 가능한 필드 업데이트
    target_user.name = name
    target_user.department = department
    target_user.phone = phone
    target_user.email = email

    db.commit()
    db.refresh(target_user)

    # 4. 수정 완료 후 리다이렉트 or 메시지
    # 여기서는 유저 리스트 페이지로 돌려보낸다고 가정
    return RedirectResponse(url="/admin/userlist", status_code=303)