from sqlalchemy import Column, Integer, String, Boolean, DateTime, func, ForeignKey, LargeBinary
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class User(Base):                                                           # 사용자 ####################################
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)                      # 사용자 인덱스 번호
    admin = Column(Boolean, nullable=False, default=False)                  # 관리자 여부, True = 관리자 / False = 일반 사용자
    employee_id = Column(String, unique=True, nullable=False)               # 사번 (으로 로그인을 함)
    password = Column(String, nullable=False)                               # 비밀번호 (해싱된 패스워드)
    name = Column(String, nullable=False)                                   # 사용자 이름
    email = Column(String, unique=True, nullable=False)                     # 사용자 이메일
    department = Column(String, nullable=False)                             # 소속부서
    phone = Column(String, nullable=True)                                   # 전화번호
    alert = Column(Integer, nullable=False, default=0)                      # 유저 알림 목록(Ex> 장비 예지보전 알림)
    message = Column(Integer, nullable=False, default=0)                    # 유저 메시지 목록(Ex> qna 관리자 답변 알림)
    created_at = Column(DateTime(timezone=True), server_default=func.now()) # 계정 생성일(자동 기록)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())       # 계정 정보 수정일(자동 기록)

class Notice(Base):                                                         # 공지사항 ######################################
    __tablename__ = "notice"
    id = Column(Integer, primary_key=True, index=True)                      # 공지사항 번호
    title = Column(String, nullable=False)                                  # 공지사항 제목
    content = Column(String, nullable=False)                                # 공지사항 내용
    user_id = Column(String, ForeignKey("users.employee_id"))               # 공지사항 작성자 사번
    created_at = Column(String)                                             # 공지사항 최초 작성일자 (YYYY-MM-DD HH:MM:SS)
    updated_at = Column(String)                                             # 공지사항 최종 수정일자 (YYYY-MM-DD HH:MM:SS), 최초 게시글 생성시 null, 수정 발생시 갱신
    public = Column(Boolean, default=True)                                  # 공개 여부, 초기 게시엔 True / 이후 비공개 설정시 False
    
    # attachment file                                                       #### 첨부파일 관련 Column, 첨부파일이 없다면 파일명, 데이터는 null
    attachment_filename = Column(String, nullable=True)                     # 공지사항 첨부파일 이름름
    attachment_content_type = Column(String, nullable=True)                 # 공지사항 첨부파일 형식, 첨부파일이 없다면 application/octet-stream
    attachment_data = Column(LargeBinary, nullable=True)                    # 공지사항 첨부파일 데이터
    
    author = relationship("User")

class QnA(Base):                                                            # 질의응답 #######################################
    __tablename__ = "qna"
    id = Column(Integer, primary_key=True, index=True)                      # 질의응답 번호
    title = Column(String, nullable=False)                                  # 질의응답 문의 제목
    content = Column(String, nullable=False)                                # 질의응답 문의 내용
    user_id = Column(String, ForeignKey("users.employee_id"))               # 질의응답 문의 작성자 사번
    created_at = Column(String)                                             # 질의응답 최초 작성일자 (YYYY-MM-DD HH:MM:SS)
    updated_at = Column(String)                                             # 질의응답 최종 수정일자 (YYYY-MM-DD HH:MM:SS), 최초 게시글 생성시 null, 수정 발생시 갱신
    public = Column(Boolean, default=False)                                 # 공개 여부,  False = 작성자(user_id), 관리자만 열람 가능 / True = 모든 사용자 열람 가능능
    
    # attachment file                                                       ### 첨부파일 관련 Column, 첨부파일이 없다면 파일명, 데이터는 null
    attachment_filename = Column(String, nullable=True)                     # 질의응답 첨부파일 이름
    attachment_content_type = Column(String, nullable=True)                 # 질의응답 첨부파일 형식, 첨부파일이 없다면 application/octet-stream
    attachment_data = Column(LargeBinary, nullable=True)                    # 질의응답 첨부파일 데이터 
    
    # reply information                                                     ### 답변 관련 Column, 답변이 존재하지 않는 경우 4개의 Column 모두 null
    reply_user = Column(String, nullable=True)                              # 질의응답 답변 작성자 사번
    reply_title = Column(String, nullable=True)                             # 질의응답 답변 제목
    reply_content = Column(String, nullable=True)                           # 질의응답 답변 내용
    reply_at = Column(String, nullable=True)                                # 질의응답 답변 작성일자 (YYYY-MM-DD HH:MM:SS)
    
    alert = Column(Boolean, nullable=False, default=False)                  # 게시물 답변 알림

    author = relationship("User")
    
class DeviceList(Base):                                                     # 장비목록 ########################################
    __tablename__ = "device_list"
    
    index = Column(Integer, primary_key=True, index=True)                   # 장비목록 인덱스 번호
    device_id = Column(String, primary_key=True)                            # 장비 이름 device_name
    device_type = Column(String)                                            # 장비 종류 OHT / AGV --> Enum? or not?
    manufacturer = Column(String)                                           # 장비 제조사
    recent_state = Column(Integer)                                          # 최근 장비상태
    
class OperationLog(Base):                                                   # 가동기록 #######################################
    __tablename__ = "operation_log"
    
    index = Column(Integer, primary_key=True, index=True)                   # 로그고유번호
    device_id = Column(String)                                              # 장비 이름
    collection_time = Column(String)                                        # 측정 시간 (YYYY-MM-DD HH:MM:SS)
    cumulative_operating_day = Column(Integer)                              # 누적 가동일
    equipment_history = Column(Integer)                                     # 장비 이력
    
                                                                            # 센서 데이터 Sensor data
    NTC = Column(Integer, nullable=False)                                   # 온도 측정값           (단위 : ℃)
    PM1_0 = Column('PM1_0', Integer, nullable=False)                        # 미세먼지 측정값 PM1.0 (단위 : µg/m3)
    PM2_5 = Column('PM2_5', Integer, nullable=False)                        # 미세먼지 측정값 PM2.5 (단위 : µg/m3) 
    PM10 = Column(Integer, nullable=False)                                  # 미세먼지 측정값 PM10  (단위 : µg/m3)
    CT1 = Column(Integer, nullable=False)                                   # 전류 측정값 CT1       (단위 : A)
    CT2 = Column(Integer, nullable=False)                                   # 전류 측정값 CT2       (단위 : A)
    CT3 = Column(Integer, nullable=False)                                   # 전류 측정값 CT3       (단위 : A)
    CT4 = Column(Integer, nullable=False)                                   # 전류 측정값 CT4       (단위 : A)
    
                                                                            # 외부 데이터 External Data
    ex_temperature = Column(Integer, nullable=False)                        # 외부 온도             (단위 : ℃)
    ex_humidity = Column(Integer, nullable=False)                           # 외부 습도             (단위 : %)
    ex_illuminance = Column(Integer, nullable=False)                        # 외부 조도             (단위 : lux)
    
