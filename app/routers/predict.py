from fastapi import APIRouter, Form, Depends, HTTPException, Request, File, Response
from sqlalchemy.orm import Session
from sqlalchemy import desc, func # 목록 최신순 출력을 위한 내림차순 추가
from app.database import SessionLocal
from app.models import DeviceList, OperationLog

from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.requests import Request
from fastapi.templating import Jinja2Templates

from datetime import datetime # 현재 시간 형태 제대로 바꾸기 위해, ex) 2025-01-16T05:14:04 -> 2025-01-16 05:14:04
from typing import List, Optional
from urllib.parse import quote # 한글 파일명 인코딩 목적
from math import ceil # pagination 계산 목적

from app.routers import auth # 사용자 토큰

router = APIRouter()

templates = Jinja2Templates(directory="templates")

@router.get("", response_class=HTMLResponse) # address/predict (뒤에 슬래시 없음) 로 받으려면 "" 
def list_device(
    request: Request,
    # page: int = 1, # 장비 목록 페이지 번호
    # limit: int = 10, # 페이지당 출력할 장비 수
    db: Session = Depends(lambda: SessionLocal()),
    current_user: dict = Depends(auth.get_current_user_from_cookie)
):
    
    # 전체 장비 수
    # total_count = db.query(func.count(DeviceList.index)).scalar()
    # total_pages = ceil(total_count / limit) if total_count else 1
    # if page < 1:
    #     page = 1
    # elif page > total_pages:
    #     page = total_pages
        
    # offset_val = (page - 1) * limit
    # devices = (db.query(DeviceList).order_by(DeviceList.index).offset(offset_val).limit(limit).all())
    devices = db.query(DeviceList).order_by(DeviceList.index).all()
    device_list = [
        {
            "device_id" : device.device_id,
            "recent_state" : device.recent_state
        }
        for device in devices
    ]
    
    # start_page = max(1, page - 4)
    # end_page = start_page + 9
    # if end_page > total_pages:
    #     end_page = total_pages
        
    # if (end_page - start_page) < 9:
    #     start_page = max(1, end_page - 9)
        
    # page_range = range(start_page, end_page + 1)
    
    # default, first device
    if devices:
        first_device_id = devices[0].device_id
        latest_record = db.query(OperationLog).filter(OperationLog.device_id == first_device_id).order_by(OperationLog.index.desc()).first()
        if latest_record:
            record_data = {
                "device_id" : latest_record.device_id,
                "PM1_0" : latest_record.PM1_0,
                "PM2_5" : latest_record.PM2_5,
                "PM10" : latest_record.PM10,
                "NTC" : latest_record.NTC,
                "CT1" : latest_record.CT1,
                "CT2" : latest_record.CT2,
                "CT3" : latest_record.CT3,
                "CT4" : latest_record.CT4,
                "collection_time": latest_record.collection_time,
                "cumulative_operating_day": latest_record.cumulative_operating_day,
                "ex_temperature": latest_record.ex_temperature,
                "ex_humidity": latest_record.ex_humidity,
                "ex_illuminance": latest_record.ex_illuminance
            }
    print(record_data)
    return templates.TemplateResponse(
        "predict.html",
        {
            "request" : request,
            "deviceList" : device_list,
            "current_user" : current_user['sub'],
            "record_data" : record_data
            # "current_page": page,
            # "total_pages": total_pages,
            # "page_range": page_range,
            # "total_count": total_count
        }
    )

    
# 장비 상세정보 조회
@router.get("/{device_id}", response_class=HTMLResponse, response_model=None)
def get_device_info(
    device_id: str,
    request: Request,
    db: Session = Depends(lambda: SessionLocal()),
    # page: int = 1,
    # total_pages: int = 10,
    # device_list: List[dict] = None
):
    latest_record = db.query(OperationLog).filter(OperationLog.device_id == device_id).order_by(OperationLog.index.desc()).first()
    if not latest_record:
        raise HTTPException(status_code=404, detail="Device data not found")
   
    record_data = {
        "device_id" : latest_record.device_id,
        "PM1_0" : latest_record.PM1_0,
        "PM2_5" : latest_record.PM2_5,
        "PM10" : latest_record.PM10,
        "NTC" : latest_record.NTC,
        "CT1" : latest_record.CT1,
        "CT2" : latest_record.CT2,
        "CT3" : latest_record.CT3,
        "CT4" : latest_record.CT4,
        "collection_time": latest_record.collection_time,
        "cumulative_operating_day": latest_record.cumulative_operating_day,
        "ex_temperature": latest_record.ex_temperature,
        "ex_humidity": latest_record.ex_humidity,
        "ex_illuminance": latest_record.ex_illuminance
    }
    
    # if device_list is None:
    #     device_list = []
    print(record_data)
    return templates.TemplateResponse(
        "predict.html",
        {
            "request": request,
            "record_data": record_data,
            
            # "current_page": page,
            # "total_pages": total_pages,
            
            # "deviceList": device_list
        }
    )
