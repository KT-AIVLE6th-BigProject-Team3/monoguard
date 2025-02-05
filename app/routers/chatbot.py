from fastapi import APIRouter, HTTPException, Depends
from functools import partial
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from langchain.chains import RetrievalQA
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chat_models import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain.agents import initialize_agent, AgentType, Tool
from app.models import OperationLog  # 데이터 모델 추가
from app.utils import get_db
from. import chatbot_tools as CT
import os, re

router = APIRouter()

# 전역 변수
qa_chain = None
openai_api_key = None

# OpenAI API 키 로드
def load_file(filepath):
    with open(filepath, 'r') as file:
        return file.readline().strip()

# 벡터스토어 및 QA 체인 초기화 함수
def initialize_chatbot():
    global qa_chain, openai_api_key
    
    try:
        # API 키 로드 및 환경변수 설정
        openai_api_key = load_file('chatbot/api_key.txt')
        os.environ['OPENAI_API_KEY'] = openai_api_key

        # 벡터스토어 로드
        embeddings_model = OpenAIEmbeddings(openai_api_key=openai_api_key)
        vectorstore = FAISS.load_local("chatbot/faiss_index", embeddings_model, allow_dangerous_deserialization=True)

        # QA 체인 설정
        prompt = PromptTemplate.from_template(
            """당신은 질문-답변(Question-Answering)을 수행하는 친절한 AI 어시스턴트입니다.
            주어진 문맥(context)에서 질문(question)에 답하세요.
            문맥에서 답을 찾을 수 없으면 `주어진 정보에서 질문에 대한 정보를 찾을 수 없습니다`라고 답하세요.

            # 질문:
            {question}

            # 문맥:
            {context}

            # 답변: (자세하게 작성해주세요)
            """
        )
        llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7)

        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            retriever=vectorstore.as_retriever(),
            chain_type_kwargs={"prompt": prompt},
            return_source_documents=True
        )

        print("📢 챗봇 초기화 완료!")
    except Exception as e:
        print(f"🚨 초기화 중 오류 발생: {e}")

def qa_chain_tool_func(query: str) -> str:
    result = qa_chain.invoke({"query": query})
    return result["result"]


# FastAPI 시작 시 챗봇 초기화
initialize_chatbot()


@router.get("/api")
async def chat_endpoint(question: str, db: Session = Depends(get_db)):
    """챗봇 API 엔드포인트"""
    global qa_chain
    if qa_chain is None:
        raise HTTPException(status_code=500, detail="챗봇이 초기화되지 않았습니다.")

    try:
        response = qa_chain.invoke({"query": question})
        return {"answer": response["result"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))





'''
@router.get("/api")
async def chat_endpoint(question: str, db: Session = Depends(get_db)):
    # 챗봇 API 엔드포인트
    """
      1. 사용자가 도구가 필요한 질문(예: 특정 날짜의 기기 데이터 요구)을 전달하면,
      2. 에이전트가 질문을 분석하여 적절한 도구를 선택 및 호출하고,
      3. 도출된 결과를 가공하여 최종 답변을 반환하도록 하였습니다.
      일반적인 질문에 대한 답변은 성공적으로 생성되지만, DB 형식이 맞지 않아 특정 데이터를 조회하는 툴은 작동을 하지 않습니다.
      models 라우터의 OperationLog과 DeviceList를 기준으로 구현했는데, 이 부분이 수정이 필요합니다.
    """
    
    tools = [
        Tool(
            name="qa_chain_tool",
            func=qa_chain_tool_func,
            description=(
                "일반 질문에 대한 답변을 생성"
                "예를 들어, '모노가드는 어떤 서비스를 수행하나요?', 'AGV란 무엇인가요?'등 용어에 대한 질문과 같은 일반적인 질문을 처리"
                "단순한 용어를 물어보는 질문에는 구체적인 설명이 필요 없음"
            ),
        ),
        Tool(
            name="query_device_status",
            func=partial(CT.query_device_status, db),
            description=(
                "특정 날짜 또는 기간 동안의 기기 상태 조회. "
                "입력은 날짜 또는 기간을 포함하는 문자열. "
                "예: '2024-02-01 기기 상태 조회' 또는 '2024-02-01 ~ 2024-02-05 동안의 기기 상태'"
            ),
        ),
        Tool(
            name="get_risky_devices",
            func=partial(CT.get_risky_devices, db),
            description=(
                "현재 위험한 상태의 기기 목록 조회. "
                "예: '현재 위험한 기기 목록 출력'"
            ),
        ),
        Tool(
            name="get_latest_device_status",
            func=partial(CT.get_latest_device_status, db),
            description=(
                "특정 기기의 최신 상태 조회. "
                "입력은 기기 ID를 포함하는 문자열. "
                "예: 'AGV-01의 최신 상태 알려줘'"
            ),
        ),
        Tool(
            name="get_all_devices_status",
            func=partial(CT.get_all_devices_status, db),
            description=(
                "모든 기기의 현재 상태 요약 출력. "
                "예: '모든 기기의 현재 상태 알려줘'"
            ),
        ),
    ]

    # LLM 인스턴스 생성 (이미 초기화된 API 키를 사용합니다)
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7)

    # 에이전트 초기화: 에이전트는 질문에 따라 어떤 도구를 사용할지 스스로 판단합니다.
    agent = initialize_agent(
        tools,
        llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
    )

    try:
        # 에이전트가 질문을 분석하여 필요한 경우 도구를 호출하고, 최종 답변을 생성합니다.
        answer = agent.run(question)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
'''