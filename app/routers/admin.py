from fastapi import APIRouter, Form, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import desc # 목록 최신순 출력을 위한 내림차순 추가
from app.database import SessionLocal
from app.models import User

router = APIRouter() 
templates = Jinja2Templates(directory="templates")

@router.get("/userlist", response_class=HTMLResponse)
def list_user(
    request: Request,
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
    
    return templates.TemplateResponse(
        "admin/user_management.html",
        {
            "request": request,
            "userList": user_list,
            "current_page": page,
            "limit": limit,
        }
    )
    
@router.delete("/delete_user/{user_id}")
def delete_user(user_id: int, db: Session = Depends(lambda: SessionLocal())):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()

    return JSONResponse(content={"message": "User deleted successfully"}, status_code=200)