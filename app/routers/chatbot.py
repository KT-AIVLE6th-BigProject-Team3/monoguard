from fastapi import APIRouter, HTTPException
from langchain.chains import RetrievalQA
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chat_models import ChatOpenAI
from langchain_core.prompts import PromptTemplate
import os

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

# FastAPI 시작 시 챗봇 초기화
initialize_chatbot()

@router.get("/api")
async def chat_endpoint(question: str):
    """챗봇 API 엔드포인트"""
    global qa_chain
    if qa_chain is None:
        raise HTTPException(status_code=500, detail="챗봇이 초기화되지 않았습니다.")

    try:
        response = qa_chain.invoke({"query": question})
        return {"answer": response["result"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
