from fastapi import FastAPI, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine
from app.models import Base
from app.routers import auth, board, user, admin, predict, chatbot
 
Base.metadata.create_all(bind=engine)
templates = Jinja2Templates(directory="templates")
app = FastAPI() 

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(user.router, prefix="/users", tags=["Users"])
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(board.router, prefix="/board", tags=["Board"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])
app.include_router(predict.router, prefix="/predict", tags=["Predict"])
app.include_router(chatbot.router, prefix="/chatbot", tags=["ChatBot"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request, current_user: dict = Depends(auth.get_current_user_from_cookie)):
    if current_user is not None:
        return templates.TemplateResponse("index.html", {"request": request, "user": current_user})
    return templates.TemplateResponse("login.html", {"request": request})
 
@app.get("/signup", response_class=HTMLResponse)
def act_register_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@app.get("/home", response_class=HTMLResponse)
def act_main_page(request: Request, current_user: dict = Depends(auth.get_current_user_from_cookie)):
    if current_user is None:
        return RedirectResponse(url="/error?code=invalid_token", status_code=303)
    return templates.TemplateResponse("index.html", {"request": request, "user": current_user})

@app.get("/notice", response_class=HTMLResponse)
def act_notice_page(current_user: dict = Depends(auth.get_current_user_from_cookie)):
    return RedirectResponse(url="/board/notice/list")

@app.get("/board/notice", response_class=HTMLResponse) # 일단 이렇게 접속할 경우가 있을까 싶지만
def redirect_notice_page(current_user: dict = Depends(auth.get_current_user_from_cookie)):
    return RedirectResponse(url="/board/notice/list")

@app.get("/notice_detail", response_class=HTMLResponse)
def act_notice_detail_page(current_user: dict = Depends(auth.get_current_user_from_cookie)):
    return templates.TemplateResponse("notice_page.html", {"request": {}, "user": current_user})

@app.get("/qna", response_class=HTMLResponse)
def act_qna_page(current_user: dict = Depends(auth.get_current_user_from_cookie)):
    return RedirectResponse(url="/board/qna/list")

@app.get("/board/qna", response_class=HTMLResponse) # 설마 이렇게 들어갈까 싶지만 아무튼
def redirect_qna_page(current_user: dict = Depends(auth.get_current_user_from_cookie)):  
    return RedirectResponse(url="/board/qna/list")

@app.get("/qna_detail", response_class=HTMLResponse)
def act_qna_detail_page(current_user: dict = Depends(auth.get_current_user_from_cookie)):
    return templates.TemplateResponse("QnA_page.html", {"request": {}, "user": current_user}) 

@app.get("/predict", response_class=HTMLResponse)
def act_predict_page(current_user: dict = Depends(auth.get_current_user_from_cookie)):
    return templates.TemplateResponse("predict.html", {"request": {}, "user": current_user}) 

@app.get("/chat", response_class=HTMLResponse)
def act_chat_page(current_user: dict = Depends(auth.get_current_user_from_cookie)):
    return templates.TemplateResponse("chat.html", {"request": {}, "user": current_user})  

@app.get("/sidebar", response_class=HTMLResponse)
def get_sidebar(current_user: dict = Depends(auth.get_current_user_from_cookie)):
    return templates.TemplateResponse("sidebar.html", {"request": {}, "user": current_user})

@app.get("/topbar", response_class=HTMLResponse)
def get_topbar(current_user: dict = Depends(auth.get_current_user_from_cookie)):
    return templates.TemplateResponse("topbar.html", {"request": {}, "user": current_user})

@app.get("/error")
def error_page(request: Request, code: str = None):
    return templates.TemplateResponse("error.html", {"request": request, "code": code})

# Admin 페이지는 admin 라우터에서 관리하도록 하였습니다.

@app.get("/auth/current_user", response_class=JSONResponse)
def get_current_user_api(current_user: dict = Depends(auth.get_current_user_from_cookie)):
    if current_user is None:
        return JSONResponse(content={"error": "User not authenticated"}, status_code=401)
    return JSONResponse(content=current_user)


@app.get("/admin/equipment_management", response_class=HTMLResponse)
def act_equip_management_page(current_user: dict = Depends(auth.get_current_user_from_cookie)):
    return templates.TemplateResponse("admin/equipment_management.html", {"request": {}, "user": current_user})

# # for predict.html page
# @app.get("/predict", response_class=HTMLResponse)
# def act_predict_page(current_user: dict = Depends(auth.get_current_user_from_cookie)):
#     return templates.TemplateResponse("predict.html", {"request": {}, "user": current_user})


