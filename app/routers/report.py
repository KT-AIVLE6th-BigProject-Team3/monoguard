# 기본 Python 라이브러리
import os
import sys
import json
import requests
import xml.etree.ElementTree as ET
 
# 외부 라이브러리
import pandas as pd
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from weasyprint import HTML  # ✅ WeasyPrint 추가
 
# OpenAI 관련 라이브러리
import openai
from openai import OpenAI
 
# LangChain 관련 라이브러리
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.chat_models import ChatOpenAI
 
import joblib
from datetime import datetime
from langchain.chains import LLMChain
from fastapi.responses import FileResponse
from pydantic import BaseModel  # ✅ Pydantic 가져오기
 
router = APIRouter()

# 전역 변수
qa_chain = None
openai_api_key = None
 
# 🔹 PDF 저장 경로 설정
REPORTS_DIR = "reports"
os.makedirs(REPORTS_DIR, exist_ok=True)  # 📂 폴더가 없으면 자동 생성
 
# ✅ 유틸리티 함수들
def load_file(filepath):
    with open(filepath, "r") as file:
        return file.readline().strip()
 
 
def load_csv(file_path):
    try:
        df = pd.read_csv(file_path, encoding="euc-kr")
        print(f"Loaded {len(df)} rows and {len(df.columns)} columns.")
        return df
    except UnicodeDecodeError:
        raise ValueError("Error: Unable to decode the file. Please check the file encoding.")
 
 
def extract_text_data(df):
    if {"구분", "내용"}.issubset(df.columns):
        return [f"구분: {row['구분']}\n내용: {row['내용']}" for _, row in df.iterrows()]
    else:
        raise ValueError("The required columns ('구분', '내용') are not found in the CSV file.")
 
 
def split_texts(text_data, chunk_size=1000, chunk_overlap=100):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    split_docs = []
    for text in text_data:
        split_docs.extend(text_splitter.split_text(text))
    print(f"Split into {len(split_docs)} chunks.")
    return split_docs
 
 
def create_vectorstore(split_docs, embeddings_model):
    try:
        vectorstore = FAISS.from_texts(split_docs, embeddings_model)
        print("Embeddings created and vectorstore generated.")
        return vectorstore
    except Exception as e:
        raise RuntimeError(f"Error during embeddings creation: {e}")
 
 
def save_vectorstore(vectorstore, path):
    vectorstore.save_local(path)
    print(f"Vectorstore saved locally as '{path}'.")
 
 
def load_vectorstore(path, embeddings_model):
    return FAISS.load_local(path, embeddings_model, allow_dangerous_deserialization=True)
 
 
def setup_qa_chain(vectorstore):
    prompt = PromptTemplate.from_template(
        """당신은 질문-답변(Question-Answering)을 수행하는 친절한 AI 어시스턴트입니다. 당신의 임무는 주어진 문맥(context) 에서 주어진 질문(question) 에 답하는 것입니다.
        검색된 다음 문맥(context) 을 사용하여 질문(question) 에 답하세요. 만약, 주어진 문맥(context) 에서 답을 찾을 수 없다면, 답을 모른다면 `주어진 정보에서 질문에 대한 정보를 찾을 수 없습니다` 라고 답하세요.
        한글로 답변해 주세요. 단, 기술적인 용어나 이름은 번역하지 않고 그대로 사용해 주세요.
 
        #Question:
        {question}
 
        #Context:
        {context}
 
        #Answer: (자세하게 작성해주세요)"""
    )
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7)
 
    return RetrievalQA.from_chain_type(
        llm=llm,
        retriever=vectorstore.as_retriever(),
        chain_type_kwargs={"prompt": prompt},
        return_source_documents=True
    )
 
 
# ✅ 앱 시작 시 초기화
@router.on_event("startup")
async def startup_event():
    global qa_chain, openai_api_key
    
    try:
        # API 키 로드 및 환경변수 설정
        openai_api_key = load_file("./chatbot/api_key.txt")
        os.environ["OPENAI_API_KEY"] = openai_api_key
 
        # CSV 로드 및 텍스트 추출
        file_path = "./report/example.csv"
        df = load_csv(file_path)
        text_data = extract_text_data(df)
 
        # 텍스트 분할
        split_docs = split_texts(text_data)
 
        # 임베딩 모델 및 벡터스토어 설정
        embeddings_model = OpenAIEmbeddings(openai_api_key=openai_api_key)
        vectorstore = create_vectorstore(split_docs, embeddings_model)
        save_vectorstore(vectorstore, "faiss_index")
 
        # 벡터스토어 로드 및 QA 체인 설정
        vectorstore = load_vectorstore("faiss_index", embeddings_model)
        qa_chain = setup_qa_chain(vectorstore)
 
        print("routerlication successfully initialized!")
    except Exception as e:
        print(f"Error during initialization: {e}")
        sys.exit(1)
 
# ✅ 챗봇 API 엔드포인트
@router.get("/")
def read_root():
    return {"message": "Welcome to QA Chatbot API!"}
 
@router.get("/chat-bot")
async def chat_endpoint(question: str):
    global qa_chain
    try:
        if qa_chain is None:
            raise HTTPException(status_code=500, detail="QA chain not initialized")
        
        response = qa_chain.invoke({"query": question})
        return response["result"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
 
# ✅ PDF 보고서 생성 (WeasyPrint 사용)
def generate_pdf_report(html_content, filename):
    pdf_path = os.path.join(REPORTS_DIR, filename)
    HTML(string=html_content).write_pdf(pdf_path)
    return pdf_path
# ✅ EquipmentReportRequest 모델 정의 추가
class EquipmentReportRequest(BaseModel):
    장비_ID: str
    시작_날짜: str  # MM-DD 형식
    종료_날짜: str  # MM-DD 형식
    
@router.post("/generate-equipment-report")
async def generate_equipment_report(request: EquipmentReportRequest):
    try:
        # ✅ HTML 보고서 생성
        html_content = f"""
        <html>
        <head><meta charset="UTF-8"></head>
        <body>
            <h1>{request.장비_ID} 정비 보고서</h1>
            <p>운영 기간: {request.시작_날짜} ~ {request.종료_날짜}</p>
            <h2>AI 분석 보고</h2>
            <p>장비의 상태에 대한 분석 결과가 여기에 포함됩니다.</p>
        </body>
        </html>
        """
 
        # ✅ PDF 파일 생성
        pdf_filename = f"{request.장비_ID}_report.pdf"
        pdf_path = generate_pdf_report(html_content, pdf_filename)
 
        # ✅ 응답 반환
        return {
            "message": "보고서 생성 완료",
            "pdf_filename": pdf_filename,
            "download_url": f"/rep/download-report/{pdf_filename}",
        }
 
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
 
@router.get("/download-report/{filename}")
async def download_report(filename: str):
    file_path = os.path.join(REPORTS_DIR, filename)
    if not os.path.exists(file_path):
        return {"error": "파일을 찾을 수 없습니다."}
    return FileResponse(file_path, filename=filename, media_type="routerlication/pdf")
 