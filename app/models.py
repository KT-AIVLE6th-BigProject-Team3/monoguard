from sqlalchemy import Column, Integer, String, Boolean, DateTime, func, ForeignKey, LargeBinary
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class User(Base): 
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)                      # 자동 생성 번호
    admin = Column(Boolean, nullable=False, default=False)                  # 일반 사용자, 관리자 여부
    employee_id = Column(String, unique=True, nullable=False)               # 사번(으로 로그인을 함)
    password = Column(String, nullable=False)                               # 해싱된 패스워드
    name = Column(String, nullable=False)                                   # 사용자 이름
    email = Column(String, unique=True, index=True, nullable=False)         # 사용자 이메일
    department = Column(String, nullable=False)                             # 부서
    phone = Column(String, nullable=True)                                    # 전화번호
    alert = Column(Integer, nullable=False, default=0)                      # 유저 알림 목록(Ex> 장비 예지보전 알림 등)
    #message = Column(Integer, nullable=False, default=0)                    # 유저 메시지 목록(Ex> 관리자 메시지)
    created_at = Column(DateTime(timezone=True), server_default=func.now()) # 계정 생성일(자동 기록)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())       # 계정 정보 수정일(자동 기록)

class Notice(Base):
    __tablename__ = "notice"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content = Column(String, nullable=False)
    user_id = Column(String, ForeignKey("users.employee_id"))
    created_at = Column(String)
    updated_at = Column(String)
    
    # attachment file
    attachment_filename = Column(String, nullable=True)
    attachment_content_type = Column(String, nullable=True)
    attachment_data = Column(LargeBinary, nullable=True)
    
    author = relationship("User")

class QnA(Base):
    __tablename__ = "qna"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content = Column(String, nullable=False)
    user_id = Column(String, ForeignKey("users.employee_id"))
    created_at = Column(String)
    updated_at = Column(String)
    
    # attachment file
    attachment_filename = Column(String, nullable=True)
    attachment_content_type = Column(String, nullable=True)
    attachment_data = Column(LargeBinary, nullable=True)
    
    # reply information
    reply_user = Column(String, nullable=True)
    reply_title = Column(String, nullable=True)
    reply_content = Column(String, nullable=True)
    reply_at = Column(String, nullable=True)

    author = relationship("User")
    
class EquipmentData(Base):
    __tablename__ = "equipment_data"
    
    device_id = Column(String, primary_key=True, index=True)
    device_manufacturer = Column(String, nullable=False)
    device_name = Column(String, nullable=False)
    installation_environment = Column(String)
    collection_time = Column(String) # collection date and time
    cumulative_operationd_day = Column(Integer)
    equipment_history = Column(Integer)
    
    # Sensor data
    PM10 = Column(Integer, nullable=False)
    PM2_5 = Column('PM2_5', Integer, nullable=False) # 소수점의 점 자 안되서 python 환경에서 돌릴 땐 2_5, 1_0 
    PM1_0 = Column('PM1_0', Integer, nullable=False)
    NTC = Column(Integer, nullable=False)
    CT1 = Column(Integer, nullable=False)
    CT2 = Column(Integer, nullable=False)
    CT3 = Column(Integer, nullable=False)
    CT4 = Column(Integer, nullable=False)
    
    # External Data
    ex_temperature = Column(Integer, nullable=False)
    ex_humidity = Column(Integer, nullable=False)
    ex_illuminance = Column(Integer, nullable=False)
    
    
#     CREATE DATABASE IF NOT EXISTS sensor_data;
# CREATE TABLE agv_data (
#     device_id VARCHAR(10),
#     collection_date DATE,
#     collection_time TIME,
#     cumulative_operating_day TINYINT,
#     filenames TEXT,
#     NTC FLOAT,
#     PM1_0 FLOAT,
#     PM2_5 FLOAT,
#     PM10 FLOAT,
#     CT1 FLOAT,
#     CT2 FLOAT,
#     CT3 FLOAT,
#     CT4 FLOAT,
#     ex_temperature FLOAT,
#     ex_humidity FLOAT,
#     ex_illuminance FLOAT
# );
# CREATE TABLE oht_data (
#     device_id VARCHAR(10),
#     collection_date DATE,
#     collection_time TIME,
#     cumulative_operating_day TINYINT,
#     filenames TEXT,
#     NTC FLOAT,
#     PM1_0 FLOAT,
#     PM2_5 FLOAT,
#     PM10 FLOAT,
#     CT1 FLOAT,
#     CT2 FLOAT,
#     CT3 FLOAT,
#     CT4 FLOAT,
#     ex_temperature FLOAT,
#     ex_humidity FLOAT,
#     ex_illuminance FLOAT
# );