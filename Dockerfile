# Python 3.12 slim 버전 사용
FROM python:3.12-slim

# 노출할 포트 지정
EXPOSE 8000

# 기본 패키지 설치 (한글 폰트 포함)
RUN apt-get update && apt-get install -y --no-install-recommends \
    locales fonts-nanum fonts-noto-cjk \
    libglib2.0-dev libcairo2 libpango1.0-0 \
    libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev \
    shared-mime-info gir1.2-glib-2.0 gobject-introspection \
    && echo "ko_KR.UTF-8 UTF-8" > /etc/locale.gen \
    && locale-gen ko_KR.UTF-8 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 환경 변수 설정 (UTF-8 적용)
ENV LANG=ko_KR.UTF-8
ENV LANGUAGE=ko_KR:ko
ENV LC_ALL=ko_KR.UTF-8

# Install pip requirements
COPY requirements.txt .
RUN python -m pip install --upgrade pip setuptools wheel
RUN python -m pip install -r requirements.txt

# 작업 디렉토리 설정
WORKDIR /app
COPY . /app

# 🔹 `.env` 파일을 컨테이너 내부로 정확히 복사
COPY .env /app/.env

# 🔹 실행 시 `.env` 파일을 자동으로 로드
ENTRYPOINT ["sh", "-c", "export $(grep -v '^#' /app/.env | xargs) && uvicorn main:app --host 0.0.0.0 --port 8000 --reload"]

# "--log-level", "info" 는 나중에 넣자 