from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from datetime import datetime
from app.models import OperationLog
from langchain.tools import tool

# 특정 날짜 또는 기간 동안의 기기 상태 조회
@tool("query_device_status")
def query_device_status(db: Session, start_date: str = None, end_date: str = None):
    """
    특정 날짜 또는 기간 동안의 기기 상태를 조회하는 함수.
    사용 예: "2024-02-01 기기 상태 조회", "2024-02-01 ~ 2024-02-05 동안의 기기 상태"
    """
    query = db.query(OperationLog)

    if start_date and end_date:
        query = query.filter(and_(OperationLog.collection_time >= start_date, OperationLog.collection_time <= end_date))
    elif start_date:
        query = query.filter(OperationLog.collection_time >= start_date)

    query = query.order_by(desc(OperationLog.collection_time)).all()

    if not query:
        return "📌 해당 날짜의 기기 데이터가 없습니다."

    response = "📢 선택된 기간 동안의 기기 상태:\n"
    for log in query[:5]:  # 너무 많으면 상위 5개만 표시
        response += (
            f"- 기기 ID: {log.device_id}\n"
            f"- 수집 시간: {log.collection_time}\n"
            f"- PM1.0: {log.PM1_0}, PM2.5: {log.PM2_5}, PM10: {log.PM10}\n"
            f"- 온도: {log.ex_temperature}°C, 습도: {log.ex_humidity}%\n\n"
        )

    return response


# 현재 위험한 상태의 기기 목록 출력
@tool("get_risky_devices")
def get_risky_devices(db: Session, pm10_threshold: int = 50):
    """
    현재 위험한 상태(예: PM10이 일정 기준 초과)인 기기 목록을 조회하는 함수.
    사용 예: "현재 위험한 기기 목록 출력"
    """
    query = db.query(OperationLog).filter(OperationLog.PM10 > pm10_threshold).order_by(desc(OperationLog.collection_time)).all()

    if not query:
        return "✅ 현재 위험 상태에 있는 기기가 없습니다."

    response = "🚨 위험 상태의 기기 목록:\n"
    for log in query[:5]:  # 위험한 기기가 많으면 상위 5개만 표시
        response += (
            f"- 기기 ID: {log.device_id} (PM10: {log.PM10})\n"
            f"- 최근 측정 시간: {log.collection_time}\n"
        )

    return response


# 특정 기기의 최신 상태 조회
@tool("get_latest_device_status")
def get_latest_device_status(db: Session, device_id: str):
    """
    특정 기기의 가장 최신 상태를 조회하는 함수.
    사용 예: "AGV-01의 최신 상태 알려줘"
    """
    log = db.query(OperationLog).filter(OperationLog.device_id == device_id).order_by(desc(OperationLog.collection_time)).first()

    if not log:
        return f"📌 기기 {device_id}에 대한 최근 데이터가 없습니다."

    return (
        f"📢 {device_id}의 최신 상태:\n"
        f"- 수집 시간: {log.collection_time}\n"
        f"- PM1.0: {log.PM1_0}, PM2.5: {log.PM2_5}, PM10: {log.PM10}\n"
        f"- 온도: {log.ex_temperature}°C, 습도: {log.ex_humidity}%\n"
    )


# 현재 모든 기기의 요약 정보 출력
@tool("get_all_devices_status")
def get_all_devices_status(db: Session):
    """
    현재 등록된 모든 기기의 최신 상태를 요약하여 반환하는 함수.
    사용 예: "모든 기기의 현재 상태 알려줘"
    """
    query = db.query(OperationLog).order_by(desc(OperationLog.collection_time)).all()

    if not query:
        return "📌 현재 등록된 기기 데이터가 없습니다."

    response = "📢 모든 기기의 최신 상태 요약:\n"
    for log in query[:5]:  # 기기가 많으면 상위 5개만 표시
        response += (
            f"- 기기 ID: {log.device_id} (PM10: {log.PM10}, 온도: {log.ex_temperature}°C)\n"
        )

    return response
