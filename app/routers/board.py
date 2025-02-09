from fastapi import APIRouter, Form, Depends, HTTPException, Request, File, Response, UploadFile # HTTPException, Request, File, Response, UploadFile 추가
from sqlalchemy.orm import Session
from sqlalchemy import desc, func # 목록 최신순 출력을 위한 내림차순 추가
from app.models import QnA, Notice
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.requests import Request
from fastapi.templating import Jinja2Templates
from datetime import datetime # 현재 시간 형태 제대로 바꾸기 위해, ex) 2025-01-16T05:14:04 -> 2025-01-16 05:14:04
from typing import List, Optional
from urllib.parse import quote # 한글 파일명 인코딩 목적
from math import ceil # pagination 계산 목적
from app.routers import auth # 사용자 토큰
from app.utils import get_db

router = APIRouter()

templates = Jinja2Templates(directory="templates")

# existing = 조회 / 수정 / 삭제 함수에서 해당 id 게시글(이 존재하는지) 저장
################ 게시글 작성
@router.post("/qna/create")
async def create_question(
    title: str = Form(...),
    content: str = Form(...),
    user_id: dict = Depends(auth.get_current_user_from_cookie),
    attachment: UploadFile = File(None),
    public: bool = Form(False),
    db: Session = Depends(get_db)
):
    new_question = QnA(title=title, content=content, user_id=user_id['sub'], created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), public=public)
    
    if attachment:
        file_content = await attachment.read()
        new_question.attachment_filename = attachment.filename
        new_question.attachment_content_type = attachment.content_type
        new_question.attachment_data = file_content
    
    db.add(new_question)
    db.commit()
    return {"message": "게시글이 성공적으로 등록되었습니다."}

# 목록 조회
@router.get("/qna/list", response_class=HTMLResponse)
def list_question(
    request: Request,
    page: int = 1,  # 페이지 번호 기본값 1
    limit: int = 10,  # 페이지당 출력할 게시글 수
    my_question: bool = False, # 작성자가 본인인 게시글을 조회하는지?
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.get_current_user_from_cookie)
):
    
    query = db.query(QnA).order_by(desc(QnA.created_at))
    # my_question이 True가 되어 접속중인 사용자가 작성한 글 목록만 조회하고 싶다면
    if my_question:
        query = query.filter(QnA.user_id == current_user['sub'])
    
    # 전체 게시글 수
    # total_count = db.query(func.count(QnA.id)).scalar()
    total_count = query.count()
    total_pages = ceil(total_count / limit) if total_count else 1
    if page < 1:
        page = 1
    elif page > total_pages:
        page = total_pages
        
    # qnas = db.query(QnA).order_by(desc(QnA.created_at)).offset(page * limit).limit(limit).all()
    offset_val = (page - 1) * limit
    qnas = (query.offset(offset_val).limit(limit).all())

    # 목록 데이터 변환 (alert 필드 추가)
    qna_list = [
        {
            "id": qna.id,
            "public" : qna.public,
            "title": qna.title,
            "user_id" : qna.user_id,
            "created_at": qna.created_at,
            "reply_title": qna.reply_title,  # 답변 여부 확인
            "alert": qna.alert
        }
        for qna in qnas
    ]

    start_page = max(1, page - 4)
    end_page = start_page + 9
    if end_page > total_pages:
        end_page = total_pages
        
    if (end_page - start_page) < 9:
        start_page = max(1, end_page - 9)

    page_range = range(start_page, end_page + 1)

    return templates.TemplateResponse(
        "QnA.html",
        {
            "request": request,
            "qnaList": qna_list,
            "current_user": current_user['sub'],
            "current_page": page,
            "total_pages": total_pages,
            "page_range": page_range,
            "total_count": total_count,
            "my_question": my_question
        }
    )
    
# 특정 게시글 조회
@router.get("/qna/content/{id}", response_class=HTMLResponse)
def read_question(
    request: Request,
    id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.get_current_user_from_cookie)
):
    existing = db.query(QnA).filter(QnA.id == id).first()
    if not existing:
        return RedirectResponse(url=f"/board/qna/list?error=notexist", status_code=303)
    if not current_user['admin'] and (current_user['sub'] != existing.user_id and existing.public is False):
        print(current_user['admin'])
        return RedirectResponse(url=f"/board/qna/list?error=no_permission", status_code=303)
    # 작성자가 본인 게시글을 조회하면 alert 해제
    if existing.user_id == current_user['sub']:
        existing.alert = False
        db.commit()
   
    qna_content = {
        "id" : existing.id,
        "user_id" : existing.user_id,
        "title" : existing.title,
        "content" : existing.content,
        "created_at" : existing.created_at,
        "updated_at" : existing.updated_at,
        "public" : existing.public,
        "reply_user" : existing.reply_user,
        "reply_title" : existing.reply_title,
        "reply_content" : existing.reply_content,
        "reply_at" : existing.reply_at,
        "filename": existing.attachment_filename,
        "content_type": existing.attachment_content_type,
        "current_user": current_user['sub'],
        "admin": current_user['admin']
    }
    return templates.TemplateResponse(
        "QnA_page.html",
        {
            "request" : request,
            "qna_content" : qna_content
        }
    )
    

# QnA 첨부파일 다운로드    
@router.get("/qna/download/{file_id}")
def download_qna_file(file_id: int,     db: Session = Depends(get_db)):
    qna = db.query(QnA).filter(QnA.id == file_id).first()
    if not qna or not qna.attachment_data:
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")

    filename = quote(qna.attachment_filename)
    content_type = qna.attachment_content_type
    file_data = qna.attachment_data
    
    headers = {
        "Content-Disposition": f"attachment; filename*=UTF-8''{filename}"
    }
    return Response(content=file_data, media_type=content_type, headers=headers)

# 게시글 수정
@router.put("/qna/content/{id}/edit")
def edit_question(
    id: int,
    title: str = Form(...),
    content: str = Form(...),
    public: bool = Form(False),
    db: Session = Depends(get_db)
):
    existing = db.query(QnA).filter(QnA.id == id).first() # 기존 content 이름을 existing으로 하여 입력받는 게시글 내용(content)와 이름 중복 방지
    if not existing:
        raise HTTPException(status_code=404, detail="존재하지 않는 QnA 게시글입니다.")

    existing.title = title
    existing.content = content
    existing.public = public
    existing.updated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
    db.commit()
    db.refresh(existing)
    
    return {
        "id": existing.id,
        "title": existing.title,
        "content": existing.content,
        "created_at": existing.created_at
    }

# 게시글 답변
@router.put("/qna/content/{id}/reply")
def reply_question(
    id: int,
    reply_title: str = Form(...),
    reply_content: str = Form(...),
    db: Session = Depends(get_db),
    reply_id: dict = Depends(auth.get_current_user_from_cookie)
):
    existing = db.query(QnA).filter(QnA.id == id).first()
    if not existing:
        raise HTTPException(status_code=404, detail="존재하지 않는 QnA 게시글입니다.")
    
    existing.reply_user = reply_id['sub']
    existing.reply_title = reply_title
    existing.reply_content = reply_content
    existing.reply_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    existing.alert = True  # 답변을 달면 alert 상태 활성화

    db.commit()
    db.refresh(existing)
    
    return {
        "message": "답변이 성공적으로 등록되었습니다.",
        "id": existing.id,
        "reply_user": existing.reply_user,
        "reply_title": existing.reply_title,
        "reply_content": existing.reply_content,
        "reply_at": existing.reply_at,
        "alert": existing.alert
    }


# 게시글 삭제
@router.delete("/qna/content/{id}/delete")
def delete_qna(
    id: int,
    db: Session = Depends(get_db)
):
    existing = db.query(QnA).filter(QnA.id == id).first()
    if not existing:
        raise HTTPException(status_code=404, detail="존재하지 않는 QnA 게시글입니다.")
    db.delete(existing)
    db.commit()
    return {"message": "QnA 게시글이 삭제되었습니다."}


##################### 공지사항(Notice)
@router.post("/notice/create")
async def create_notice(
    title: str = Form(...),
    content: str = Form(...),
    user_id: dict = Depends(auth.get_current_user_from_cookie),
    attachment: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    print("user_id", user_id)
    new_notice = Notice(title=title, content=content, user_id=user_id['sub'], created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    if attachment:
        file_content = await attachment.read()
        new_notice.attachment_filename = attachment.filename
        new_notice.attachment_content_type = attachment.content_type
        new_notice.attachment_data = file_content
    
    db.add(new_notice)
    db.commit()
    return {"message": "게시글이 성공적으로 등록되었습니다!"}

# 목록 조회
@router.get("/notice/list", response_class=HTMLResponse)
def list_notice(
    request: Request,
    page: int = 0, # 목록 페이지 번호
    limit: int = 10, # 페이지당 출력할 게시글 수
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.get_current_user_from_cookie)
):
    
    # admin일 경우
    if current_user['admin']:
        # 전체 게시글 수
        total_count = db.query(func.count(Notice.id)).scalar()
        query = db.query(Notice)
    else: # admin이 아닐 경우, 공개된 공지사항만
        total_count = db.query(func.count(Notice.id)).filter(Notice.public == True).scalar()
        query = db.query(Notice).filter(Notice.public == True)
        
    total_pages = ceil(total_count / limit) if total_count else 1
    if page < 1:
        page = 1
    elif page > total_pages:
        page = total_pages
    
    offset_val = (page - 1) * limit
    notices = (query.order_by(desc(Notice.created_at)).offset(offset_val).limit(limit).all())
    notice_list = [
        {
            "id" : notice.id,
            "title" : notice.title,
            "writer" : notice.user_id, # user_id가 아닌 writer를 사용함에 유의
            "public" : notice.public,
            "created_at" : notice.created_at
        }
        for notice in notices
    ]
    
    template_name = "notice.html"
    start_page = max(1, page - 4)
    end_page = start_page + 9
    if end_page > total_pages:
        end_page = total_pages
        
    if (end_page - start_page) < 9:
        start_page = max(1, end_page - 9)
        
    page_range = range(start_page, end_page + 1)
    
    return templates.TemplateResponse(
        template_name,
        {
            "request" : request,
            "noticeList" : notice_list,
            "current_page": page,
            "total_pages": total_pages,
            "page_range": page_range,
            "total_count": total_count,
            "admin" : current_user['admin']
        }
    )

# 특정 게시글 조회
@router.get("/notice/content/{id}", response_class=HTMLResponse)
def read_notice(
    request: Request,
    id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth.get_current_user_from_cookie)
):
    existing = db.query(Notice).filter(Notice.id == id).first()
    if not existing:
        raise HTTPException(status_code=404, detail="존재하지 않는 공지글입니다.")
    
    # 이전글 정보 조회
    prev_notice = (db.query(Notice).filter(Notice.id < existing.id).order_by(Notice.id.desc()).first())
    # 다음글 정보 조회
    next_notice = (db.query(Notice).filter(Notice.id > existing.id).order_by(Notice.id.asc()).first())
    
    # Notice 첨부파일 목록 조회
    notice_content = {
            "id" : existing.id,
            "user_id" : existing.user_id,
            "title" : existing.title,
            "content" : existing.content,
            "created_at" : existing.created_at,
            "updated_at" : existing.updated_at,
            "public" : existing.public,
            "current_user": current_user['sub'],
            "admin": current_user['admin'],
            "files" : [
                {
                    "filename": existing.attachment_filename,
                    "content_type": existing.attachment_content_type,
                    "id": existing.id,
                }
            ] if existing.attachment_filename else []
    }
    
    return templates.TemplateResponse(
        "notice_page.html",
        {
            "request" : request,
            "notice_content" : notice_content,
            "prev_notice" : {
                "id": prev_notice.id,
                "title": prev_notice.title
            } if prev_notice else None,
            "next_notice":{
                "id": next_notice.id,
                "title": next_notice.title
            } if next_notice else None
        }
    )
    
# 공지사항 첨부파일 다운로드    
@router.get("/notice/download/{file_id}")
def download_notice_file(file_id: int,     db: Session = Depends(get_db)):
    notice = db.query(Notice).filter(Notice.id == file_id).first()
    if not notice or not notice.attachment_data:
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")

    filename = notice.attachment_filename
    content_type = notice.attachment_content_type
    file_data = notice.attachment_data
    
    encoded_filename = quote(filename)
    headers = {
        "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
    }
    return Response(content=file_data, media_type=content_type, headers=headers)

# 게시글 수정
@router.put("/notice/content/{id}/edit")
def edit_notice(
    id: int,
    title: str = Form(...),
    content: str = Form(...),
    public: bool = Form(False),
    db: Session = Depends(get_db)
):
    existing = db.query(Notice).filter(Notice.id == id).first() # 기존 content 이름을 existing으로 하여 입력받는 게시글 내용(content)와 이름 중복 방지
    if not existing:
        raise HTTPException(status_code=404, detail="존재하지 않는 공지글입니다.")
    if title:
        existing.title = title
    if content:
        existing.content = content
    existing.public = public
    existing.updated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
    db.commit()
    db.refresh(existing)
    
    return {
        "id": existing.id,
        "title": existing.title,
        "content": existing.content,
        "created_at": existing.created_at
    }

# 게시글 삭제
@router.delete("/notice/content/{id}/delete")
def delete_notice(
    id: int,
db: Session = Depends(get_db)
):
    existing = db.query(Notice).filter(Notice.id == id).first()
    if not existing:
        raise HTTPException(status_code=404, detail="존재하지 않는 공지글입니다.")
    db.delete(existing)
    db.commit()
    return {"message": "공지사항 게시글이 삭제되었습니다."}
