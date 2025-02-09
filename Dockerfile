# Python Slim 이미지 사용
FROM python:3.12-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 설치 (필요한 경우)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libopenblas-dev \
        libssl-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# pip, setuptools 최신화
RUN python -m pip install --upgrade pip setuptools wheel

# requirements.txt 복사 및 패키지 설치
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# 애플리케이션 코드 및 데이터베이스 파일 복사
COPY main.py /app/
COPY firstdb.db /app/
COPY db.sqlite3 /app/

# 포트 노출 (FastAPI 예제 기준)
EXPOSE 8000

# FastAPI 애플리케이션 실행
ENTRYPOINT ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--log-level", "info"]
