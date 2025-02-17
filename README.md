# MONOGUARD
## 🚀 AI 기반 스마트 운송장치 예지보전 솔루션

MONOGUARD는 제조 멀티모달 데이터를 활용하여 이동식 장비(OHT, AGV)의 모니터링과 고장 예측 및 상태 분석을 제공하는 AI 기반의 산업 안전 솔루션입니다.
<p align="center">
  <img src="https://github.com/user-attachments/assets/d24a424e-b3d9-4092-a9d7-716270be46c8" alt="AI 3조 썸네일"/>
</p>


---

## 🔥 주요 서비스

### ✅ 예지보전
- 제조 멀티모달 데이터를 분석하여 장비의 이상 징후를 감지하고, 고장을 사전에 예측합니다.

### ✅ 실시간 모니터링
- 장비 상태 및 장비에 부착된 센서 데이터를 실시간으로 분석하여 최적의 운영 상태를 유지합니다.

### ✅ AI 챗봇
- 장비 상태를 진단하고, 고장 원인을 확인하여 매뉴얼과 해결책을 제안합니다.

### ✅ 자동 보고서 생성
- 사전 설정된 형식에 따라 장비 정보를 분석하고, 결과를 자동으로 제공합니다.

---

## 🎯 목표 고객
B2B 반도체 공정 제조사 (예: 삼성전자, SK 하이닉스, 현대자동차 등)

---

## 🏆 기대 효과
- 제조 공정의 **안전성 및 생산성 강화**
- 장비 고장 및 인명 사고 예방
- 유지보수 비용 절감으로 경제적 효과 극대화
- **AI 기반 예측 정확도 90%**, 하루 약 80만 원의 비용 절감 효과

---

# 사용 스택
## 🔹 프론트엔드 (FE)
<div style="display: flex; gap: 8px;">
    <img src="https://img.shields.io/badge/-HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white"/>
    <img src="https://img.shields.io/badge/-CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white"/>
    <img src="https://img.shields.io/badge/-JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black"/>
    <img src="https://img.shields.io/badge/-Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white"/>
</div>

## 🔹 백엔드 (BE)
<div style="display: flex; gap: 8px;">
    <img src="https://img.shields.io/badge/-Python-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
    <img src="https://img.shields.io/badge/-FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white"/>
    <img src="https://img.shields.io/badge/-SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white"/>
    <img src="https://img.shields.io/badge/-Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white"/>
</div>

## 🔹 클라우드 & 인프라
<div style="display: flex; gap: 8px;">
    <img src="https://img.shields.io/badge/-Azure-0078D4?style=for-the-badge&logo=microsoftazure&logoColor=white"/>
</div>

## 🔹 AI & 데이터
<div style="display: flex; gap: 8px;">
    <img src="https://img.shields.io/badge/-AI%20Hub-FF9900?style=for-the-badge"/>
    <img src="https://img.shields.io/badge/-PyTorch-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white"/>
</div>

## 🔹 협업 툴
<div style="display: flex; gap: 8px;">
    <img src="https://img.shields.io/badge/-GitHub-181717?style=for-the-badge&logo=github&logoColor=white"/>
    <img src="https://img.shields.io/badge/-Teams-6264A7?style=for-the-badge&logo=microsoftteams&logoColor=white"/>
    <img src="https://img.shields.io/badge/-Notion-000000?style=for-the-badge&logo=notion&logoColor=white"/>
    <img src="https://img.shields.io/badge/-Figma-F24E1E?style=for-the-badge&logo=figma&logoColor=white"/>
</div>


---

## 📌 서비스 플로우
1. **데이터 수집**: 열화상 이미지, 센서 데이터 수집
2. **실시간 모니터링**: 장비 상태 및 이상 징후 감지
3. **AI 분석**: 고장 예측 및 유지보수 추천
4. **사용자 알림**: 대시보드를 통한 실시간 피드백
5. **챗봇 대응**: 원인 분석 및 해결 방안 제시
6. **자동 보고서 생성**: 분석 결과 기반 맞춤형 리포트 제공

---
## 🎬 1분만에 알아보는 MonoGuard
[![MonoGuard 소개 영상](https://img.youtube.com/vi/47dXqLPG-XE/maxresdefault.jpg)](https://youtu.be/47dXqLPG-XE)


## 🚀 실행 방법
### 1️⃣ 프로젝트 클론
```bash
git clone https://github.com/your-repo/monoguard.git
cd monoguard
```

### 2️⃣ 가상환경 설정 및 패키지 설치
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3️⃣ 서비스 실행
```bash
uvicorn main:app
```
```bash
streamlit run dashboard.py
```
