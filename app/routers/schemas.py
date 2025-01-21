from pydantic import BaseModel
from typing import Optional

class QnaBase(BaseModel):
    writer_id: str
    content: str
    title: str
    date: str

# QnA 게시글 작성 요청 스키마
class QnaCreate(QnaBase):
    pass

# QnA 게시글 수정 요청 스키마
class QnaUpdate(BaseModel):
    content: str
    title: str
    
# QnA 게시글 답변 요청 스키마
class QnaAnswer(BaseModel):
    answer_id: str # 이거는 나중에 사용자 ID(이름)이 자동으로 들어가도록
    answer_content: str
    

# 게시글 응답 스키마
class QnaResponse(QnaBase):
    qna_id: int
    answer_id: Optional[str] = None
    answer_content: Optional[str] = None

    class Config:
        orm_mode = True