# 🛡️ MONOGUARD

<div align="center">
  <img src="https://github.com/user-attachments/assets/d24a424e-b3d9-4092-a9d7-716270be46c8" alt="MonoGuard 썸네일" width="600px"/>
  <h3>멀티모달 AI 기반 스마트 운송장치 예지보전 시스템</h3>
  <p><i>하나의 시스템으로 장비 모니터링, 이상 예방, 보고서 생성 및 사용자 지원 기능 통합 제공</i></p>
  
  <p>
    <a href="#-프로젝트-배경"><img src="https://img.shields.io/badge/배경-0091EA?style=for-the-badge" alt="배경"/></a>
    <a href="#-주요-서비스"><img src="https://img.shields.io/badge/서비스-00C853?style=for-the-badge" alt="서비스"/></a>
    <a href="#-서비스-차별점"><img src="https://img.shields.io/badge/차별점-FFD600?style=for-the-badge" alt="차별점"/></a>
    <a href="#-ai-기술-설명"><img src="https://img.shields.io/badge/AI기술-D500F9?style=for-the-badge" alt="AI기술"/></a>
    <a href="#-비즈니스-가치"><img src="https://img.shields.io/badge/비즈니스-FF3D00?style=for-the-badge" alt="비즈니스"/></a>
  </p>
</div>

---

## 📊 프로젝트 정보

<div align="center">

| 항목 | 내용 |
|:---:|:---|
| **프로젝트 기간** | 2024.12.30 ~ 2025.02.14 (47일) |
| **프로젝트 유형** | KT AIVLE School 빅프로젝트 |
| **주요 성과** | 예측 정확도 90% 달성, 예상 하루 80만원 순이익 |

</div>

---

## 📚 프로젝트 배경

<table>
<tr>
<td width="60%">

### 🚨 제조업 장비 고장의 경제적 영향
- **삼성전자 평택 사업장(2018)**: 30분 공정 중단으로 **500억 원 손실**
- **미국 제조업계**: 장비 고장으로 매년 **500억 달러(약 60조 원) 손실**
- **AI 예지보전 효과**: 설비 보전 비용 10% 절감, 매출 74% 상승

### 🔄 제조 환경의 변화
- 고정형 컨베이어 벨트에서 **이동식 장비(AGV, OHT)**로 전환
- 이동식 장비는 동적 경로 설정으로 **생산 유연성 증가**
- 복잡한 운영 환경으로 인한 **새로운 모니터링 요구**

### ⚠️ 기존 예지보전 시스템의 한계
- **고정 장비 중심 설계**로 이동식 장비 대응 미흡
- **단일 데이터 소스** 의존으로 복합적 고장 패턴 감지 한계
- **정적 임계값** 사용으로 장비별 특성 반영 부족

</td>
<td width="40%">
<img src="https://github.com/user-attachments/assets/d131502b-f3a2-4adc-ada5-2e8f4ab2f6fc" alt="서비스 플로우" width="100%"/>
</td>
</tr>
</table>

---

## 🔥 주요 서비스

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px;">

<div style="border-left: 4px solid #00C853; padding-left: 20px; margin-bottom: 20px;">
  <h3>🤖 멀티모달 AI 예지보전</h3>
  <ul>
    <li><strong>열화상 이미지 + 센서 데이터</strong> 통합 분석</li>
    <li>단일모달 대비 <strong>40% 향상된 예측 정확도(90%)</strong></li>
    <li><strong>슬라이딩 윈도우</strong> 기법으로 연속적 상태 변화 감지</li>
    <li><strong>베이지안 확률</strong> 기반 신뢰도 높은 상태 분류</li>
    <li><strong>Grad-CAM</strong>으로 AI 판단 근거 시각화</li>
  </ul>
</div>

<div style="border-left: 4px solid #304FFE; padding-left: 20px; margin-bottom: 20px;">
  <h3>📊 실시간 모니터링 대시보드</h3>
  <ul>
    <li><strong>직관적 웹 인터페이스</strong>로 장비 상태 파악</li>
    <li><strong>5분 간격</strong> 실시간 데이터 업데이트</li>
    <li><strong>장비별 맞춤 알림</strong> 및 위험도 표시</li>
    <li><strong>30초 슬라이딩 윈도우</strong>로 데이터 손실 방지</li>
    <li><strong>통계 기반 동적 임계값</strong> 적용</li>
  </ul>
</div>

<div style="border-left: 4px solid #D500F9; padding-left: 20px; margin-bottom: 20px;">
  <h3>💬 RAG 기반 AI 챗봇</h3>
  <ul>
    <li><strong>LangChain + GPT-3.5</strong> 기반 정확한 응답</li>
    <li><strong>297개 QA 데이터셋</strong> 학습으로 82% 정확도</li>
    <li><strong>장비 매뉴얼, 고장 원인, 해결책</strong> 제안</li>
    <li><strong>Vector DB 최적화</strong>로 관련 정보 신속 검색</li>
    <li><strong>환각(Hallucination) 방지</strong>로 신뢰성 확보</li>
  </ul>
</div>

<div style="border-left: 4px solid #FF3D00; padding-left: 20px; margin-bottom: 20px;">
  <h3>📄 자동 보고서 생성</h3>
  <ul>
    <li><strong>Weasyprin 라이브러리</strong> 기반 PDF 생성</li>
    <li><strong>AI 프롬프트</strong> 기반 데이터 요약 및 분석</li>
    <li><strong>장비 상태, 이상 징후, 권장 조치</strong> 포함</li>
    <li><strong>관리자 업무 효율화</strong> 및 의사결정 지원</li>
    <li><strong>맞춤형 분석 보고서</strong> 자동 생성</li>
  </ul>
</div>

</div>

---

## 🌟 서비스 차별점

<table>
<tr>
<td width="50%">
<h3>🚀 이동형 장비 최적화</h3>
<ul>
  <li><strong>AGV, OHT</strong> 같은 이동형 장비 특화 모니터링</li>
  <li><strong>동적 경로 설정</strong> 장비의 유연한 상태 관리</li>
  <li><strong>현대적 제조 환경</strong>에 최적화된 솔루션</li>
  <li><strong>실시간 위치 추적</strong> 및 상태 모니터링</li>
</ul>
</td>
<td width="50%">
<h3>📊 통계 기반 동적 임계값</h3>
<ul>
  <li><strong>데이터 분포 기반</strong> 동적 임계값 적용</li>
  <li><strong>통계적 검증</strong>으로 상태 분류 유의성 확보</li>
  <li><strong>장비별 맞춤형</strong> 상태 판단 기준</li>
  <li><strong>베이지안 확률</strong>로 불확실성 정량화</li>
</ul>
</td>
</tr>
<tr>
<td>
<h3>💼 비즈니스 중심 모델 최적화</h3>
<ul>
  <li><strong>Recall(재현율) 최우선</strong> 모델 학습</li>
  <li><strong>클래스 가중치 적용</strong>으로 30% 성능 향상</li>
  <li><strong>비용 효율적</strong> 최적 균형점 도출</li>
  <li><strong>실제 현장</strong> 요구사항 반영</li>
</ul>
</td>
<td>
<h3>🧠 멀티모달 데이터 통합 분석</h3>
<ul>
  <li><strong>Cross Attention</strong>으로 이미지-센서 데이터 통합</li>
  <li><strong>ViT + Transformer</strong> 기반 효과적 특징 추출</li>
  <li><strong>단일 소스</strong>에서 놓칠 수 있는 패턴 보완</li>
  <li><strong>mmTransformer</strong> 아키텍처 구현</li>
</ul>
</td>
</tr>
</table>

---

## 💻 기술 스택

### 🎨 프론트엔드
<div style="display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 15px;">
    <img src="https://img.shields.io/badge/-HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white"/>
    <img src="https://img.shields.io/badge/-CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white"/>
    <img src="https://img.shields.io/badge/-JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black"/>
    <img src="https://img.shields.io/badge/-Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white"/>
    <img src="https://img.shields.io/badge/-Bootstrap-7952B3?style=for-the-badge&logo=bootstrap&logoColor=white"/>
</div>

### ⚙️ 백엔드
<div style="display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 15px;">
    <img src="https://img.shields.io/badge/-Python-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
    <img src="https://img.shields.io/badge/-FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white"/>
    <img src="https://img.shields.io/badge/-SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white"/>
    <img src="https://img.shields.io/badge/-Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white"/>
</div>

### 🤖 AI & 데이터 분석
<div style="display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 15px;">
    <img src="https://img.shields.io/badge/-PyTorch-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white"/>
    <img src="https://img.shields.io/badge/-OpenAI_GPT-412991?style=for-the-badge&logo=openai&logoColor=white"/>
    <img src="https://img.shields.io/badge/-LangChain-12B886?style=for-the-badge"/>
    <img src="https://img.shields.io/badge/-FAISS-00A6D6?style=for-the-badge"/>
    <img src="https://img.shields.io/badge/-Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white"/>
    <img src="https://img.shields.io/badge/-NumPy-013243?style=for-the-badge&logo=numpy&logoColor=white"/>
</div>

### ☁️ 배포 및 협업
<div style="display: flex; gap: 8px; flex-wrap: wrap;">
    <img src="https://img.shields.io/badge/-Azure-0078D4?style=for-the-badge&logo=microsoftazure&logoColor=white"/>
    <img src="https://img.shields.io/badge/-GitHub-181717?style=for-the-badge&logo=github&logoColor=white"/>
    <img src="https://img.shields.io/badge/-Teams-6264A7?style=for-the-badge&logo=microsoftteams&logoColor=white"/>
    <img src="https://img.shields.io/badge/-Notion-000000?style=for-the-badge&logo=notion&logoColor=white"/>
</div>

---

## 🧠 AI 기술 설명

<div align="center">
  <img src="https://github.com/user-attachments/assets/d147dca8-d5ba-4e25-a2ea-e5de0d3cfe1f" alt="AI 아키텍처" width="80%"/>
  <h4>멀티모달 Transformer 기반 예지보전 아키텍처</h4>
</div>

### 🔄 데이터 처리 파이프라인

#### 1️⃣ **입력 데이터 전처리**

#### 2️⃣ **특징 추출 및 임베딩**
- **ViT (Vision Transformer)**: 열화상 이미지를 16×16 패치로 분할하여 공간적 특징 추출
- **Soft Label Encoder**: 센서 데이터의 시간적 패턴 및 상관관계 학습
- **Cross Attention**: 이미지-센서 데이터 간 관계성 모델링

#### 3️⃣ **상태 분류 및 예측**
```python
# 4단계 장비 상태 분류
status_mapping = {
    0: "정상 (Normal)",
    1: "관심 (Attention)", 
    2: "주의 (Caution)",
    3: "위험 (Critical)"
}
```

### 📊 모델 성능 비교

<div align="center">

| 모델 유형 | 입력 데이터 | 정확도 | Recall | 특징 |
|:-------:|:-------:|:------:|:------:|:------|
| **단일모달** | 이미지만 | 53% | 53% | ViT 기반, 이미지 패턴만 분석 |
| **멀티모달** | 이미지+센서 | **90%** | **90%** | Cross Attention으로 데이터 통합 |
| **개선율** | - | **+37%** | **+37%** | 클래스 가중치 적용 최적화 |

</div>

### 🎯 모델 최적화 전략

- **비즈니스 우선순위**: Recall > Precision (고장 미감지 최소화)
- **클래스 불균형 해결**: 가중치 적용으로 성능 30% 향상
- **베이지안 확률**: 예측 불확실성 정량화로 신뢰도 제공

---

## 💰 비즈니스 가치

<table>
<tr>
<td width="50%">


### 💡 ROI 분석
- **일일 순이익**: 약 **80만원** (90% 정확도 기준,기대 가치 계산 공식 기준)
- **연간 예상 수익**: 약 **2억 9천만원**

</td>
<td width="50%">

### ⚖️ 비용 효율성 분석

| 항목 | 비용 | 영향도 |
|:---:|:---:|:---:|
| **고장 미감지 (FN)** | 수십억 원 | 🔴 매우 높음 |
| **불필요 유지보수 (FP)** | 수천만 원 | 🟡 보통 |
| **AI 시스템 운영** | 수백만 원 | 🟢 낮음 |

### 🎯 핵심 성과 지표
- **예측 정확도**: 90%
- **Recall (재현율)**: 90%
- **실시간 모니터링**: 5분 간격
- **챗봇 정확도**: 82%

</td>
</tr>
</table>

---

## 🚀 실행 방법

### 1️⃣ 프로젝트 설정

```bash
# 저장소 클론
git clone https://github.com/your-username/monoguard.git
cd monoguard

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 2️⃣ 환경 변수 설정

```bash
# .env 파일 생성
cp .env.example .env

# 필요한 API 키 설정
OPENAI_API_KEY=your_openai_api_key
AZURE_ENDPOINT=your_azure_endpoint
```

### 3️⃣ 서비스 실행

```bash
# 백엔드 API 서버 실행
uvicorn app.main:app --reload --port 8000

# 새 터미널에서 대시보드 실행
streamlit run dashboard/app.py --server.port 8501
```

### 4️⃣ Docker 실행 (선택사항)

```bash
# Docker 이미지 빌드
docker build -t monoguard .

# 컨테이너 실행
docker run -p 8000:8000 -p 8501:8501 monoguard
```

### 🌐 접속 URL
- **API 서버**: http://localhost:8000
- **대시보드**: http://localhost:8501
- **API 문서**: http://localhost:8000/docs

---

## 📽️ 시연 영상

<div align="center">
  <a href="https://youtu.be/47dXqLPG-XE">
    <img src="https://img.youtube.com/vi/47dXqLPG-XE/maxresdefault.jpg" alt="MonoGuard 소개 영상" width="600px"/>
  </a>
  <br>
  <strong>🎬 클릭하면 YouTube에서 시연 영상을 볼 수 있습니다</strong>
</div>

---

## 🏆 주요 성과 및 학습

### 🎯 기술적 성과
- **멀티모달 AI 모델**: 단일모달 대비 37% 성능 향상
- **실시간 시스템**: 5분 간격 안정적 모니터링 구현
- **API 최적화**: 호출 주기 최적화로 서버 비용 절감
- **RAG 시스템**: Vector DB 재구조화로 20% 정확도 향상

### 💡 비즈니스 역량
- **현장 중심 개발**: 실제 제조업 요구사항 반영한 솔루션 설계
- **비용 효율성**: Recall 중심 최적화로 비즈니스 가치 극대화
- **사용자 경험**: 직관적 대시보드와 챗봇으로 접근성 향상

### 📚 학습 내용
- **멀티모달 데이터 처리**: 이미지와 센서 데이터 통합 방법론
- **Transformer 아키텍처**: Cross Attention 메커니즘 구현
- **예지보전 도메인**: 제조업 현장의 실제 문제와 해결 방안
- **MLOps**: 모델 배포, 모니터링, 최적화 전 과정

---

<div align="center">
  <h3> KT AIVLE School 빅프로젝트 | MONOGUARD Team | 2024-2025</h3>
</div>
