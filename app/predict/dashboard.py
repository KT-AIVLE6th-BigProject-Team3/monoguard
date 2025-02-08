import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import json
import plotly.graph_objects as go
import numpy as np


# ✅ Streamlit 페이지 설정 (가장 먼저 실행해야 함)
st.set_page_config(page_title="장비 모니터링 대시보드", layout="wide")

# ✅ URL 쿼리 매개변수 확인 (query_params 사용)
query_params = st.query_params
page = query_params.get("page", "AGV 상태 분포")  # 기본값 설정
embed_mode = query_params.get("embed", "false").lower() == "true"  # embed=true이면 True

# ✅ 데이터베이스 연결 함수
def get_db_connection():
    return sqlite3.connect("sensor_data.db")

# ✅ 모든 페이지에서 Streamlit UI 요소 제거 (상단 색깔 선, Deploy 버튼 등)
st.markdown("""
    <style>
        /* Streamlit 기본 스타일 제거 */
        header {visibility: hidden;}
        .stDeployButton {display: none !important;} /* Deploy 버튼 숨기기 */
        [data-testid="stDecoration"] {display: none !important;} /* 색깔 선 제거 */
        [data-testid="stToolbar"] {display: none !important;} /* 점 세 개(⋮) 숨기기 */
        .block-container { padding-top: 0rem; padding-bottom: 0rem; }  /*위아래 여백 제거*/
        /* 사이드바 완전히 숨기기 */
        [data-testid="stSidebar"] {display: none !important;}
        section[data-testid="stSidebarContent"] {display: none !important;}
        /* 특정 버튼 숨기기 */
        button[aria-label=""] {
            display: none !important;
        }
    </style>
""", unsafe_allow_html=True)

# ✅ AGV 상태 분포
def agv_status_distribution():
    conn = get_db_connection()
    query = """
        WITH latest_status AS (
            SELECT device_id, MAX(aggregation_end) as latest_time
            FROM aggregated_device_status
            WHERE device_id IN ('AGV17', 'AGV18')
            GROUP BY device_id
        )
        SELECT 
            a.device_id,
            a.status as current_status,
            a.normal_ratio,
            a.caution_ratio,
            a.warning_ratio,
            a.risk_ratio
        FROM aggregated_device_status a
        INNER JOIN latest_status l 
        ON a.device_id = l.device_id AND a.aggregation_end = l.latest_time
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    if df.empty:
        st.warning("⚠️ 현재 AGV 장비 데이터가 없습니다.")
    else:
        # API와 동일한 방식으로 상태 카운팅
        status_counts = df['current_status'].value_counts()
        
        # 파이 차트 생성
        fig = px.pie(
            values=status_counts.values,
            names=status_counts.index,
            title="AGV 상태 분포 (장비 수)",
            color=status_counts.index,
            color_discrete_map={
                "정상": "#28a745",
                "관심": "#ffc107",
                "경고": "#fd7e14",
                "위험": "#dc3545"
            }
        )
        
        fig.update_traces(
            textinfo='value',
            texttemplate='%{value}대',
            hovertemplate='%{label}<br>%{value}대<extra></extra>',
            textposition='inside',
            textfont=dict(size=20, color='white')
        )
        
        fig.update_layout(
            height=300,
            margin=dict(l=20, r=20, t=30, b=20),
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)



# ✅ AGV 경고 및 위험 장비 (`aggregated_device_status` 기반)
def agv_warning_risk():
    conn = get_db_connection()
    query = """
        SELECT device_id, normal_ratio, caution_ratio, warning_ratio, risk_ratio
        FROM aggregated_device_status
        WHERE device_id LIKE 'AGV%'
        ORDER BY risk_ratio DESC, warning_ratio DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    if df.empty:
        st.warning("⚠️ 현재 경고 및 위험 상태의 AGV 장비가 없습니다.")
    else:
        # ✅ 상태 재분류 (가장 높은 비율을 기준으로 결정)
        def classify_state(row):
            max_ratio = max(row["normal_ratio"], row["caution_ratio"], row["warning_ratio"], row["risk_ratio"])
            if max_ratio == row["risk_ratio"]:  
                return "위험"
            elif max_ratio == row["warning_ratio"]:  
                return "경고"
            elif max_ratio == row["caution_ratio"]:  
                return "관심"
            return "정상"

        df["상태"] = df.apply(classify_state, axis=1)

        # ✅ 테이블 컬럼명 변경 (가독성 향상)
        df = df.rename(columns={
            "device_id": "장비 ID",
            "normal_ratio": "정상 비율",
            "caution_ratio": "관심 비율",
            "warning_ratio": "경고 비율",
            "risk_ratio": "위험 비율"
        })

        # ✅ 경고 및 위험 상태만 필터링
        df_filtered = df[df["상태"].isin(["경고", "위험"])]

        if df_filtered.empty:
            st.warning("⚠️ 현재 경고 및 위험 상태의 AGV 장비가 없습니다.")
        else:
            # ✅ 경고 및 위험 상태 강조 색상 적용
            def color_state(val):
                if val == "경고":
                    return "background-color: #ffc107; color: black;"  # 노란색
                elif val == "위험":
                    return "background-color: #dc3545; color: white;"  # 빨간색
                return ""

            # ✅ Streamlit 스타일 적용한 테이블 표시
            st.dataframe(df_filtered.style.applymap(color_state, subset=["상태"]))

# ✅ 시간에 따른 AGV 상태 변화 (`aggregated_device_status` 기반)
def agv_status_time_series():
   conn = get_db_connection()
   query = """
       SELECT device_id, aggregation_start AS timestamp, 
              normal_ratio, caution_ratio, warning_ratio, risk_ratio,
              status as current_status
       FROM aggregated_device_status
       WHERE device_id LIKE 'AGV%'
       ORDER BY aggregation_start ASC
   """
   df = pd.read_sql_query(query, conn)
   conn.close()

   if df.empty:
       st.error("⚠️ AGV 데이터가 없습니다! DB를 확인해주세요.")
   else:
       df["timestamp"] = pd.to_datetime(df["timestamp"])
       
       # 상태 매핑
       state_mapping = {"정상": 0, "관심": 1, "경고": 2, "위험": 3}
       df["state_numeric"] = df["current_status"].map(state_mapping)
       
       # Hover 텍스트 생성
       df["hover_text"] = df.apply(
           lambda row: f"<b>{row['device_id']}</b><br>" +
                      f"<b>시간:</b> {row['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}<br>" +
                      f"<b>현재 상태:</b> {row['current_status']}<br>" +
                      f"<br><b>상태별 비율</b><br>" +
                      f"✅ 정상: {row['normal_ratio']:.1f}%<br>" +
                      f"⚠️ 관심: {row['caution_ratio']:.1f}%<br>" +
                      f"🚨 경고: {row['warning_ratio']:.1f}%<br>" +
                      f"⛔ 위험: {row['risk_ratio']:.1f}%",
           axis=1
       )

       # 각 장비별로 구분된 라인 차트 생성
       fig = go.Figure()
       
       # 장비별 색상 매핑
       colors = {
           'AGV17': '#1f77b4',  # 파란색
           'AGV18': '#2ca02c'   # 초록색
       }
       
       for device_id in df['device_id'].unique():
           device_data = df[df['device_id'] == device_id]
           
           fig.add_trace(go.Scatter(
               x=device_data["timestamp"],
               y=device_data["state_numeric"],
               name=device_id,
               mode='lines+markers',
               line=dict(
                   color=colors[device_id],
                   width=2  # 선 두께 감소
               ),
               marker=dict(
                   size=6,  # 마커 크기 감소
                   symbol='circle',
                   line=dict(
                       color='white',
                       width=1
                   )
               ),
               customdata=device_data["hover_text"],
               hovertemplate="%{customdata}<extra></extra>"
           ))

       # Y축 텍스트를 HTML로 색상 지정
       colored_labels = [
           f'<span style="color: #28a745">정상</span>',  # 초록색
           f'<span style="color: #ffc107">관심</span>',  # 노란색
           f'<span style="color: #fd7e14">경고</span>',  # 주황색
           f'<span style="color: #dc3545">위험</span>'   # 빨간색
       ]

       # 레이아웃 설정
       fig.update_layout(
           plot_bgcolor='white',  # 배경색 흰색
           paper_bgcolor='white',
           height=300,  # 차트 높이 감소
           yaxis=dict(
               ticktext=colored_labels,  # 컬러 레이블 적용
               tickvals=[0, 1, 2, 3],
               title="장비 상태",
               gridcolor='lightgray',
               zeroline=False,
               title_font=dict(size=14),
               tickfont=dict(size=12),
               range=[-0.2, 3.2]  # y축 범위 조정으로 간격 축소
           ),
           xaxis=dict(
               title="시간",
               gridcolor='lightgray',
               zeroline=False,
               title_font=dict(size=14),
               tickfont=dict(size=12),
               tickformat="%H:%M",
               nticks=20
           ),
           hovermode="x unified",
           legend=dict(
               orientation="h",
               yanchor="bottom",
               y=1.02,
               xanchor="right",
               x=1,
               bgcolor='rgba(255, 255, 255, 0.8)',
               bordercolor='lightgray'
           ),
           margin=dict(l=50, r=50, t=80, b=50)
       )

       # 상태별 색상의 구분선 추가
       status_colors = {
           0: "#28a745",  # 정상 - 초록색
           1: "#ffc107",  # 관심 - 노란색
           2: "#fd7e14",  # 경고 - 주황색
           3: "#dc3545"   # 위험 - 빨간색
       }

       # 상태 구분선 추가
       for y_val in [0, 1, 2, 3]:
           fig.add_hline(
               y=y_val,
               line_dash="solid",
               line_color=status_colors[y_val],
               line_width=2,
               opacity=0.3
           )

       st.plotly_chart(fig, use_container_width=True, key="status_time_series")

# ✅ 최근 AGV 작업 환경
def recent_environment():
    # 스타일 적용
    st.markdown("""
        <style>
        [data-testid="metric-container"] {
            width: fit-content;
            margin: auto;
        }

        [data-testid="metric-container"] > div {
            width: fit-content;
            margin: auto;
        }

        [data-testid="metric-container"] label {
            font-size: 0.6rem !important;
            color: rgba(0,0,0,0.6);
        }

        [data-testid="metric-container"] div[data-testid="metric-value"] {
            font-size: 0.8rem !important;
        }

        [data-testid="metric-container"] div[data-testid="metric-delta"] {
            font-size: 0.6rem !important;
        }

        [data-testid="stHorizontalBlock"] {
            gap: 0.5rem !important;
        }
        
        .timestamp {
            text-align: right;
            color: #666;
            font-size: 0.8rem !important;
            margin-top: 0.5rem;
            padding-right: 1rem;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # 데이터베이스 연결 및 데이터 조회
    conn = get_db_connection()
    query = """
        SELECT 
            timestamp,
            ex_temperature,
            ex_humidity,
            ex_illuminance
        FROM environment_measurements
        ORDER BY timestamp DESC
        LIMIT 1
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if df.empty:
        st.warning("⚠️ 현재 환경 데이터가 없습니다.")
        return
    
    latest_data = df.iloc[0]
    
    try:
        timestamp = pd.to_datetime(latest_data['timestamp'])
        timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
    except:
        timestamp_str = str(latest_data['timestamp'])
    
    # 메트릭 표시
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "온도",
            f"{latest_data['ex_temperature']:.1f}°C"
        )
    
    with col2:
        st.metric(
            "습도",
            f"{latest_data['ex_humidity']:.1f}%"
        )
    
    with col3:
        st.metric(
            "조도",
            f"{latest_data['ex_illuminance']:.0f}lx"
        )
    
    # 타임스탬프 표시 (더 큰 폰트 사이즈로)
    st.markdown(
        f"<div class='timestamp'>"
        f"📅 {timestamp_str}"
        f"</div>",
        unsafe_allow_html=True
    )
        
# ✅ AGV 온도 변화 
def agv_temperature_change():
    conn = get_db_connection()
    df = pd.read_sql("SELECT timestamp, ex_temperature FROM environment_measurements", conn) 
    
    if df.empty:
        st.warning("⚠️ 현재 AGV 온도 데이터가 없습니다.")
        return
    
    # 데이터 전처리 
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors='coerce')
    df = df.dropna(subset=["timestamp"])
    df["minute"] = df["timestamp"].dt.floor("min")
    df = df.groupby("minute")[["ex_temperature"]].mean().reset_index()
    conn.close()

    # 온도 임계값
    NORMAL_TEMP = 25.494680
    CAUTION_TEMP = 25.464758 
    WARNING_TEMP = 25.480036
    DANGER_TEMP = 25.480520

    # 메트릭스 스타일
    st.markdown("""
        <style>
        [data-testid="metric-container"] {
            width: fit-content;
            margin: auto;
        }

        [data-testid="metric-container"] > div {
            width: fit-content;
            margin: auto;
        }

        [data-testid="metric-container"] label {
            font-size: 0.6rem !important;
            color: rgba(0,0,0,0.6);
        }

        [data-testid="metric-container"] div[data-testid="metric-value"] {
            font-size: 0.8rem !important;
        }

        [data-testid="metric-container"] div[data-testid="metric-delta"] {
            font-size: 0.6rem !important;
        }

        .st-emotion-cache-p38tq {
            font-size: 1.6rem !important;
            color: rgb(49, 51, 63) !important;
        }

        /* 메트릭스 간격 조정 */
        [data-testid="stHorizontalBlock"] {
            gap: 0.5rem !important;
        }
                
        </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    current_temp = df["ex_temperature"].iloc[-1]
    max_temp = df["ex_temperature"].max()
    min_temp = df["ex_temperature"].min()
    temp_change = current_temp - df['ex_temperature'].iloc[-2] if len(df) > 1 else 0
    
    with col1:
        st.metric("현재 온도", f"{current_temp:.1f}°C", f"{temp_change:.1f}°C", delta_color="inverse")
    with col2:
        st.metric("최고 온도", f"{max_temp:.1f}°C")
    with col3:
        st.metric("최저 온도", f"{min_temp:.1f}°C")

    # 그래프
    fig = go.Figure()
    
    def get_temp_status_color(temp):
        if abs(temp - DANGER_TEMP) <= 0.5:
            return '#FF4444'
        elif abs(temp - WARNING_TEMP) <= 0.5:
            return '#FFA726'  
        elif abs(temp - CAUTION_TEMP) <= 0.5:
            return '#FFC107'
        return '#4CAF50'

    # 기준선
    fig.add_hline(y=DANGER_TEMP, line_dash="dash", line_color="#FF4444", annotation_text="위험")
    fig.add_hline(y=WARNING_TEMP, line_dash="dash", line_color="#FFA726", annotation_text="경고")
    fig.add_hline(y=CAUTION_TEMP, line_dash="dash", line_color="#FFC107", annotation_text="주의")

    # 온도 변화 그래프 
    fig.add_trace(go.Scatter(
        x=df["minute"],
        y=df["ex_temperature"],
        mode="lines+markers",
        line=dict(color=get_temp_status_color(current_temp), width=2),
        marker=dict(
            size=4,
            color=df["ex_temperature"].apply(get_temp_status_color)
        ),
        name="온도 변화",
        hovertemplate="<b>시간</b>: %{x|%H:%M}<br>" +
                      "<b>온도</b>: %{y:.1f}°C<br><extra></extra>"
    ))

    fig.update_layout(
        title="AGV 작업현장 온도",
        height=300,  # 높이 줄임
        margin=dict(l=20, r=20, t=40, b=20),  # 여백 줄임
        xaxis=dict(
            title=None,  # 축 제목 제거
            gridcolor='rgba(128,128,128,0.1)',
            nticks=10,  # 눈금 수 줄임
            tickformat="%H:%M"
        ),
        yaxis=dict(
            title=None,  # 축 제목 제거
            gridcolor='rgba(128,128,128,0.1)',
            range=[min(NORMAL_TEMP - 0.5, df["ex_temperature"].min() - 0.2),
                   max(DANGER_TEMP + 0.5, df["ex_temperature"].max() + 0.2)]
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        showlegend=False,
        hovermode="x unified"
    )

    st.plotly_chart(fig, use_container_width=True)

    # 상태 메시지
    def get_temp_status_message(temp):
        if abs(temp - DANGER_TEMP) <= 0.5:
            st.error("⚠️ 온도가 매우 위험한 수준입니다")
        elif abs(temp - WARNING_TEMP) <= 0.5:
            st.warning("⚠️ 온도가 높습니다")
        elif abs(temp - CAUTION_TEMP) <= 0.5:
            st.warning("📢 온도가 약간 상승했습니다")
        else:
            st.success("✅ 온도 정상")

    get_temp_status_message(current_temp)
       
# ✅ AGV 습도 변화 
def agv_humidity_change():
    conn = get_db_connection()
    df = pd.read_sql("SELECT timestamp, ex_humidity FROM environment_measurements", conn) 
    
    if df.empty:
        st.warning("⚠️ 현재 AGV 습도 데이터가 없습니다.")
        return
    
    # 임계값 설정 (sensor_distributions의 ex_humidity 기준)
    NORMAL_HUMID = 30.464285
    CAUTION_HUMID = 30.569384
    WARNING_HUMID = 30.417036
    DANGER_HUMID = 30.498701
    
    # 데이터 전처리 
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors='coerce')
    df = df.dropna(subset=["timestamp"])
    df["minute"] = df["timestamp"].dt.floor("min")
    df = df.groupby("minute")[["ex_humidity"]].mean().reset_index()
    conn.close()

    # 메트릭스 스타일
    st.markdown("""
        <style>
        .st-emotion-cache-p38tq {
            font-size: 1.6rem !important;
            color: rgb(49, 51, 63) !important;
        }
        [data-testid="metric-container"] {
            width: fit-content;
            margin: auto;
        }
        [data-testid="metric-container"] > div {
            width: fit-content;
            margin: auto;
        }
        [data-testid="metric-container"] label {
            font-size: 0.6rem !important;
            color: rgba(0,0,0,0.6);
        }
        [data-testid="metric-container"] div[data-testid="metric-value"] {
            font-size: 0.8rem !important;
        }
        [data-testid="metric-container"] div[data-testid="metric-delta"] {
            font-size: 0.6rem !important;
        }
        [data-testid="stHorizontalBlock"] {
            gap: 0.5rem !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # 메트릭스
    col1, col2, col3 = st.columns(3)
    current_humid = df["ex_humidity"].iloc[-1]
    max_humid = df["ex_humidity"].max()
    min_humid = df["ex_humidity"].min()
    humid_change = current_humid - df['ex_humidity'].iloc[-2] if len(df) > 1 else 0
    
    with col1:
        st.metric("현재 습도", f"{current_humid:.1f}%", f"{humid_change:.1f}%", delta_color="inverse")
    with col2:
        st.metric("최고 습도", f"{max_humid:.1f}%")
    with col3:
        st.metric("최저 습도", f"{min_humid:.1f}%")

    # 그래프
    fig = go.Figure()
    
    def get_humid_status_color(humid):
        if abs(humid - DANGER_HUMID) <= 0.5:
            return '#FF4444'
        elif abs(humid - WARNING_HUMID) <= 0.5:
            return '#FFA726'  
        elif abs(humid - CAUTION_HUMID) <= 0.5:
            return '#FFC107'
        return '#4CAF50'

    # 기준선
    fig.add_hline(y=DANGER_HUMID, line_dash="dash", line_color="#FF4444", annotation_text="위험")
    fig.add_hline(y=WARNING_HUMID, line_dash="dash", line_color="#FFA726", annotation_text="경고")
    fig.add_hline(y=CAUTION_HUMID, line_dash="dash", line_color="#FFC107", annotation_text="주의")
    
    # 습도 변화 그래프 
    fig.add_trace(go.Scatter(
        x=df["minute"],
        y=df["ex_humidity"],
        mode="lines+markers",
        line=dict(color=get_humid_status_color(current_humid), width=2),
        marker=dict(
            size=4,
            color=df["ex_humidity"].apply(get_humid_status_color)
        ),
        name="습도 변화",
        hovertemplate="<b>시간</b>: %{x|%H:%M}<br>" +
                      "<b>습도</b>: %{y:.1f}%<br><extra></extra>"
    ))

    fig.update_layout(
        title="AGV 외부 습도",
        height=300,
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis=dict(
            title=None,
            gridcolor='rgba(128,128,128,0.1)',
            nticks=10,
            tickformat="%H:%M"
        ),
        yaxis=dict(
            title=None,
            gridcolor='rgba(128,128,128,0.1)',
            range=[min(NORMAL_HUMID - 0.5, df["ex_humidity"].min() - 0.2),
                   max(DANGER_HUMID + 0.5, df["ex_humidity"].max() + 0.2)]
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        showlegend=False,
        hovermode="x unified"
    )

    st.plotly_chart(fig, use_container_width=True)

    def get_humid_status_message(humid):
        if abs(humid - DANGER_HUMID) <= 0.5:
            st.error("⚠️ 습도가 매우 높습니다. 즉시 확인이 필요합니다")
        elif abs(humid - WARNING_HUMID) <= 0.5:
            st.warning("⚠️ 습도가 높습니다. 환기가 필요합니다")
        elif abs(humid - CAUTION_HUMID) <= 0.5:
            st.warning("📢 습도가 약간 상승했습니다. 모니터링이 필요합니다")
        else:
            st.success("✅ 습도 정상")

    get_humid_status_message(current_humid)
       
# ✅ AGV 조도 변화 
def agv_illuminance_change():
    conn = get_db_connection()
    df = pd.read_sql("SELECT timestamp, ex_illuminance FROM environment_measurements", conn) 
    
    if df.empty:
        st.warning("⚠️ 현재 AGV 조도 데이터가 없습니다.")
        return
    
    # 임계값 설정 (sensor_distributions의 ex_illuminance 기준)
    NORMAL_ILLUM = 155.609421
    CAUTION_ILLUM = 155.480179
    WARNING_ILLUM = 155.352264
    DANGER_ILLUM = 155.241562
    
    # 데이터 전처리 
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors='coerce')
    df = df.dropna(subset=["timestamp"])
    df["minute"] = df["timestamp"].dt.floor("min")
    df = df.groupby("minute")[["ex_illuminance"]].mean().reset_index()
    conn.close()

    # 메트릭스 스타일
    st.markdown("""
        <style>
        .st-emotion-cache-p38tq {
            font-size: 1.6rem !important;
            color: rgb(49, 51, 63) !important;
        }
        [data-testid="metric-container"] {
            width: fit-content;
            margin: auto;
        }
        [data-testid="metric-container"] > div {
            width: fit-content;
            margin: auto;
        }
        [data-testid="metric-container"] label {
            font-size: 0.6rem !important;
            color: rgba(0,0,0,0.6);
        }
        [data-testid="metric-container"] div[data-testid="metric-value"] {
            font-size: 0.8rem !important;
        }
        [data-testid="metric-container"] div[data-testid="metric-delta"] {
            font-size: 0.6rem !important;
        }
        [data-testid="stHorizontalBlock"] {
            gap: 0.5rem !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # 메트릭스
    col1, col2, col3 = st.columns(3)
    current_illum = df["ex_illuminance"].iloc[-1]
    max_illum = df["ex_illuminance"].max()
    min_illum = df["ex_illuminance"].min()
    illum_change = current_illum - df['ex_illuminance'].iloc[-2] if len(df) > 1 else 0
    
    with col1:
        st.metric("현재 조도", f"{current_illum:.1f} lux", f"{illum_change:.1f} lux", delta_color="inverse")
    with col2:
        st.metric("최고 조도", f"{max_illum:.1f} lux")
    with col3:
        st.metric("최저 조도", f"{min_illum:.1f} lux")

    # 그래프
    fig = go.Figure()
    
    def get_illum_status_color(illum):
        if abs(illum - DANGER_ILLUM) <= 0.5:
            return '#FF4444'
        elif abs(illum - WARNING_ILLUM) <= 0.5:
            return '#FFA726'  
        elif abs(illum - CAUTION_ILLUM) <= 0.5:
            return '#FFC107'
        return '#4CAF50'

    # 기준선
    fig.add_hline(y=DANGER_ILLUM, line_dash="dash", line_color="#FF4444", annotation_text="위험")
    fig.add_hline(y=WARNING_ILLUM, line_dash="dash", line_color="#FFA726", annotation_text="경고")
    fig.add_hline(y=CAUTION_ILLUM, line_dash="dash", line_color="#FFC107", annotation_text="주의")
    
    # 조도 변화 그래프 
    fig.add_trace(go.Scatter(
        x=df["minute"],
        y=df["ex_illuminance"],
        mode="lines+markers",
        line=dict(color=get_illum_status_color(current_illum), width=2),
        marker=dict(
            size=4,
            color=df["ex_illuminance"].apply(get_illum_status_color)
        ),
        name="조도 변화",
        hovertemplate="<b>시간</b>: %{x|%H:%M}<br>" +
                      "<b>조도</b>: %{y:.1f} lux<br><extra></extra>"
    ))

    fig.update_layout(
        title="AGV 외부 조도",
        height=300,
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis=dict(
            title=None,
            gridcolor='rgba(128,128,128,0.1)',
            nticks=10,
            tickformat="%H:%M"
        ),
        yaxis=dict(
            title=None,
            gridcolor='rgba(128,128,128,0.1)',
            range=[min(NORMAL_ILLUM - 1, df["ex_illuminance"].min() - 0.5),
                   max(DANGER_ILLUM + 1, df["ex_illuminance"].max() + 0.5)]
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        showlegend=False,
        hovermode="x unified"
    )

    st.plotly_chart(fig, use_container_width=True)

    def get_illum_status_message(illum):
        if abs(illum - DANGER_ILLUM) <= 0.5:
            st.error("⚠️ 조도가 매우 낮습니다. 즉시 확인이 필요합니다")
        elif abs(illum - WARNING_ILLUM) <= 0.5:
            st.warning("⚠️ 조도가 낮습니다. 점검이 필요합니다")
        elif abs(illum - CAUTION_ILLUM) <= 0.5:
            st.warning("📢 조도가 약간 낮아졌습니다. 모니터링이 필요합니다")
        else:
            st.success("✅ 조도 정상")

    get_illum_status_message(current_illum)

# ✅ AGV 상태 현황 (최근 aggregation_end 기준 가장 높은 비율을 반영, 장비별 최신 데이터 보장)
def agv_device_status():
    conn = get_db_connection()
    query = """
    SELECT 
        SUM(CASE WHEN max_category = 'normal' THEN 1 ELSE 0 END) AS normal_count,
        SUM(CASE WHEN max_category = 'caution' THEN 1 ELSE 0 END) AS caution_count,
        SUM(CASE WHEN max_category = 'warning' THEN 1 ELSE 0 END) AS warning_count,
        SUM(CASE WHEN max_category = 'risk' THEN 1 ELSE 0 END) AS risk_count
    FROM (
        SELECT 
            s.device_id,
            CASE 
                WHEN s.normal_ratio >= s.caution_ratio 
                AND s.normal_ratio >= s.warning_ratio 
                AND s.normal_ratio >= s.risk_ratio THEN 'normal'
                WHEN s.caution_ratio >= s.normal_ratio 
                AND s.caution_ratio >= s.warning_ratio 
                AND s.caution_ratio >= s.risk_ratio THEN 'caution'
                WHEN s.warning_ratio >= s.normal_ratio 
                AND s.warning_ratio >= s.caution_ratio 
                AND s.warning_ratio >= s.risk_ratio THEN 'warning'
                ELSE 'risk'
            END AS max_category
        FROM aggregated_device_status s
        INNER JOIN (
            SELECT device_id, MAX(aggregation_end) AS latest_aggregation
            FROM aggregated_device_status
            WHERE device_id IN ('AGV17', 'AGV18')
            GROUP BY device_id
        ) latest ON s.device_id = latest.device_id AND s.aggregation_end = latest.latest_aggregation
    ) AS subquery;
    """
    df_status = pd.read_sql_query(query, conn)
    conn.close()
    
    if df_status.empty:
        st.warning("⚠️ 장비 상태 데이터가 없습니다.")
    else:
        normal_total = int(df_status["normal_count"].iloc[0])
        caution_total = int(df_status["caution_count"].iloc[0])
        warning_total = int(df_status["warning_count"].iloc[0])
        risk_total = int(df_status["risk_count"].iloc[0])
    
        html_content = f"""
        <style>
            .status-card {{
                display: flex;
                justify-content: space-around;
                text-align: center;
                border: 2px solid #ddd;
                border-radius: 10px;
                padding: 10px;
                margin: 10px 0;
                height: 100px;
            }}
            
            .status-box {{
                flex: 1;
                padding: 10px;
                border-right: 2px solid #ddd;
                height: 100%;
                display: flex;
                flex-direction:column;
                align-items: center;
                justify-content: center;
            }}
            .status-box:last-child {{
                border-right: none;
            }}
            .status-title {{
                font-size: 20px;
                font-weight: bold;
            }}
            .status-value {{
                font-size: 24px;
                font-weight: bold;
                color: #333;
            }}
        </style>
        <div class='status-card'>
            <div class='status-box'>
                <div class='status-title'>✅ 정상</div>
                <div class='status-value'>{normal_total}대</div>
            </div>
            <div class='status-box'>
                <div class='status-title'>⚠️ 관심</div>
                <div class='status-value'>{caution_total}대</div>
            </div>
            <div class='status-box'>
                <div class='status-title'>🚨 경고</div>
                <div class='status-value'>{warning_total}대</div>
            </div>
            <div class='status-box'>
                <div class='status-title'>⛔ 위험</div>
                <div class='status-value'>{risk_total}대</div>
            </div>
        </div>
        """
        st.markdown(html_content, unsafe_allow_html=True)

def agv_thermal_monitoring():
    st.markdown("""
        <style>
        .block-container {padding: 0;}
        .status-card {
            padding: 1rem;
            border-radius: 8px;
        }
        .status-badge {
            text-align: center;
            padding: 0.3rem 1rem;
            border-radius: 4px;
            font-weight: 500;
            margin-bottom: 0.8rem;
        }
        .temp-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1rem;
            text-align: center;
        }
        .temp-label {
            color: #858796;
            font-size: 0.8rem;
            margin-bottom: 0.3rem;
        }
        .temp-value {
            font-size: 1.2rem;
            font-weight: 500;
        }
        </style>
    """, unsafe_allow_html=True)
    
    devices = ['AGV17', 'AGV18']
    
    with st.container():
        cols = st.columns(len(devices))
        for idx, device in enumerate(devices):
            with cols[idx]:
                timestamps = pd.date_range(end=pd.Timestamp.now(), periods=60, freq='S')
                base_temp = 45 + np.sin(np.linspace(0, 2*np.pi, 60)) * 3  
                temps = base_temp + np.random.randn(60) * 0.5
                current_temp = temps[-1]
                
                if current_temp < 47:
                    status = "정상"
                    status_color = "#1cc88a"
                    status_bg = "#e6fff0"
                elif current_temp < 60:
                    status = "주의" 
                    status_color = "#f6c23e"
                    status_bg = "#fff8e6"
                elif current_temp < 75:
                    status = "경고"
                    status_color = "#fd7e14"
                    status_bg = "#fff4e6"
                else:
                    status = "위험"
                    status_color = "#e74a3b"
                    status_bg = "#ffe6e6"

                gauge_fig = go.Figure()
                gauge_fig.add_trace(go.Indicator(
                    mode="gauge+number",
                    value=current_temp,
                    number={'suffix': "°C"},
                    domain={'x': [0, 1], 'y': [0, 1]},
                    title={
                        'text': f"<b>{device}</b><br><span style='font-size:12px;color:gray'>현재 온도</span>",
                        'font': {'color': 'black', 'size': 18}
                    },
                    gauge={
                        'axis': {'range': [20, 80], 'tickwidth': 1},
                        'bar': {'color': "lightgray", 'thickness': 0.1},  # 바 색상을 연한 회색으로 변경하고 두께를 줄임
                        'bgcolor': "white",
                        'steps': [
                            {'range': [20, 47], 'color': "#1cc88a"},
                            {'range': [47, 60], 'color': "#f6c23e"},
                            {'range': [60, 75], 'color': "#fd7e14"},
                            {'range': [75, 80], 'color': "#e74a3b"}
                        ],
                        'threshold': {
                            'line': {'color': status_color, 'width': 4},  # 선 두께를 증가
                            'thickness': 1,  # threshold 두께를 증가
                            'value': current_temp
                        }
                    }
                ))

                gauge_fig.update_layout(
                    height=150,
                    margin=dict(t=30, b=10, l=30, r=30),
                    paper_bgcolor='rgba(0,0,0,0)'
                )
                
                st.plotly_chart(gauge_fig, use_container_width=True, config={'displayModeBar': False})
                
                line_fig = go.Figure()
                line_fig.add_trace(go.Scatter(
                    x=timestamps,
                    y=temps,
                    mode='lines',
                    line=dict(color=status_color, width=2)
                ))
                
                line_fig.update_layout(
                    title={
                        'text': f"{device} 열화상 센서 온도", 
                        'y':0.9,
                        'x':0.5,
                        'xanchor': 'center',
                        'yanchor': 'top'
                    },
                    height=150,
                    margin=dict(t=40, b=40, l=30, r=30),
                    showlegend=False,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    yaxis=dict(
                        range=[20, 80],
                        showgrid=True,
                        gridcolor='lightgray'
                    ),
                    xaxis=dict(
                        showgrid=True,
                        gridcolor='lightgray'
                    )
                )
                
                st.plotly_chart(line_fig, use_container_width=True, config={'displayModeBar': False})
                
                st.markdown(f"""
                    <div class="status-card">
                        <div class="status-badge" style="background: {status_bg}; color: {status_color};">
                            {status}
                        </div>
                        <div class="temp-grid">
                            <div>
                                <div class="temp-label">평균</div>
                                <div class="temp-value">{np.mean(temps):.1f}°C</div>
                            </div>
                            <div>
                                <div class="temp-label">최고</div>
                                <div class="temp-value" style="color: {status_color}">{np.max(temps):.1f}°C</div>
                            </div>
                            <div>
                                <div class="temp-label">최저</div>
                                <div class="temp-value">{np.min(temps):.1f}°C</div>
                            </div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
        
# OHT

# ✅ OHT 상태 현황 (최근 aggregation_end 기준 가장 높은 비율을 반영, 장비별 최신 데이터 보장)
def oht_device_status():
    conn = get_db_connection()
    query = """
    SELECT 
        SUM(CASE WHEN max_category = 'normal' THEN 1 ELSE 0 END) AS normal_count,
        SUM(CASE WHEN max_category = 'caution' THEN 1 ELSE 0 END) AS caution_count,
        SUM(CASE WHEN max_category = 'warning' THEN 1 ELSE 0 END) AS warning_count,
        SUM(CASE WHEN max_category = 'risk' THEN 1 ELSE 0 END) AS risk_count
    FROM (
        SELECT 
            s.device_id,
            CASE 
                WHEN s.normal_ratio >= s.caution_ratio 
                AND s.normal_ratio >= s.warning_ratio 
                AND s.normal_ratio >= s.risk_ratio THEN 'normal'
                WHEN s.caution_ratio >= s.normal_ratio 
                AND s.caution_ratio >= s.warning_ratio 
                AND s.caution_ratio >= s.risk_ratio THEN 'caution'
                WHEN s.warning_ratio >= s.normal_ratio 
                AND s.warning_ratio >= s.caution_ratio 
                AND s.warning_ratio >= s.risk_ratio THEN 'warning'
                ELSE 'risk'
            END AS max_category
        FROM aggregated_device_status s
        INNER JOIN (
            SELECT device_id, MAX(aggregation_end) AS latest_aggregation
            FROM aggregated_device_status
            WHERE device_id IN ('OHT17', 'OHT18')
            GROUP BY device_id
        ) latest ON s.device_id = latest.device_id AND s.aggregation_end = latest.latest_aggregation
    ) AS subquery;
    """
    df_status = pd.read_sql_query(query, conn)
    conn.close()
    
    if df_status.empty:
        st.warning("⚠️ 장비 상태 데이터가 없습니다.")
    else:
        normal_total = int(df_status["normal_count"].iloc[0])
        caution_total = int(df_status["caution_count"].iloc[0])
        warning_total = int(df_status["warning_count"].iloc[0])
        risk_total = int(df_status["risk_count"].iloc[0])
    
        html_content = f"""
        <style>
            .status-card {{
                display: flex;
                justify-content: space-around;
                text-align: center;
                border: 2px solid #ddd;
                border-radius: 10px;
                padding: 10px;
                margin: 10px 0;
                height: 100px;
            }}
            
            .status-box {{
                flex: 1;
                padding: 10px;
                border-right: 2px solid #ddd;
                height: 100%;
                display: flex;
                flex-direction:column;
                align-items: center;
                justify-content: center;
            }}
            .status-box:last-child {{
                border-right: none;
            }}
            .status-title {{
                font-size: 20px;
                font-weight: bold;
            }}
            .status-value {{
                font-size: 24px;
                font-weight: bold;
                color: #333;
            }}
        </style>
        <div class='status-card'>
            <div class='status-box'>
                <div class='status-title'>✅ 정상</div>
                <div class='status-value'>{normal_total}대</div>
            </div>
            <div class='status-box'>
                <div class='status-title'>⚠️ 관심</div>
                <div class='status-value'>{caution_total}대</div>
            </div>
            <div class='status-box'>
                <div class='status-title'>🚨 경고</div>
                <div class='status-value'>{warning_total}대</div>
            </div>
            <div class='status-box'>
                <div class='status-title'>⛔ 위험</div>
                <div class='status-value'>{risk_total}대</div>
            </div>
        </div>
        """
        st.markdown(html_content, unsafe_allow_html=True)
        
        
# ✅ OHT 상태 분포
def oht_status_distribution():
    conn = get_db_connection()
    query = """
        WITH latest_status AS (
            SELECT device_id, MAX(aggregation_end) as latest_time
            FROM aggregated_device_status
            WHERE device_id IN ('OHT17', 'OHT18')
            GROUP BY device_id
        )
        SELECT 
            a.device_id,
            a.status as current_status,  
            a.normal_ratio,
            a.caution_ratio,
            a.warning_ratio,
            a.risk_ratio
        FROM aggregated_device_status a
        INNER JOIN latest_status l 
        ON a.device_id = l.device_id AND a.aggregation_end = l.latest_time
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    if df.empty:
        st.warning("⚠️ 현재 OHT 장비 데이터가 없습니다.")
    else:
        # API와 동일한 방식으로 상태 카운팅
        status_counts = df['current_status'].value_counts()
        
        # Plotly 파이 차트 생성
        fig = px.pie(
            values=status_counts.values,
            names=status_counts.index,
            title="OHT 상태 분포 (장비 수)",
            color=status_counts.index,
            color_discrete_map={
                "정상": "#28a745",
                "관심": "#ffc107",
                "경고": "#fd7e14",
                "위험": "#dc3545"
            }
        )
        
        fig.update_traces(
            textinfo='value',
            texttemplate='%{value}대',
            hovertemplate='%{label}<br>%{value}대<extra></extra>',
            textposition='inside',
            textfont=dict(size=20, color='white')
        )
        
        fig.update_layout(
            height=300,
            margin=dict(l=20, r=20, t=30, b=20),
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)

# ✅ 시간에 따른 OHT 상태 변화 (`aggregated_device_status` 기반)
def oht_status_time_series():
    conn = get_db_connection()
    query = """
        SELECT device_id, aggregation_start AS timestamp, 
               normal_ratio, caution_ratio, warning_ratio, risk_ratio,
               status as current_status
        FROM aggregated_device_status
        WHERE device_id LIKE 'OHT%'
        ORDER BY aggregation_start ASC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    if df.empty:
        st.error("⚠️ OHT 데이터가 없습니다! DB를 확인해주세요.")
    else:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        
        # 상태 매핑
        state_mapping = {"정상": 0, "관심": 1, "경고": 2, "위험": 3}
        df["state_numeric"] = df["current_status"].map(state_mapping)
        
        # Hover 텍스트 생성
        df["hover_text"] = df.apply(
            lambda row: f"<b>{row['device_id']}</b><br>" +
                       f"<b>시간:</b> {row['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}<br>" +
                       f"<b>현재 상태:</b> {row['current_status']}<br>" +
                       f"<br><b>상태별 비율</b><br>" +
                       f"✅ 정상: {row['normal_ratio']:.1f}%<br>" +
                       f"⚠️ 관심: {row['caution_ratio']:.1f}%<br>" +
                       f"🚨 경고: {row['warning_ratio']:.1f}%<br>" +
                       f"⛔ 위험: {row['risk_ratio']:.1f}%",
            axis=1
        )

        # 각 장비별로 구분된 라인 차트 생성
        fig = go.Figure()
        
        # 장비별 색상 매핑
        colors = {
            'OHT16': '#1f77b4',  # 파란색
            'OHT17': '#2ca02c',  # 초록색
        }
        
        for device_id in df['device_id'].unique():
            device_data = df[df['device_id'] == device_id]
            
            fig.add_trace(go.Scatter(
                x=device_data["timestamp"],
                y=device_data["state_numeric"],
                name=device_id,
                mode='lines+markers',
                line=dict(
                    color=colors.get(device_id, '#000000'),
                    width=2
                ),
                marker=dict(
                    size=6,
                    symbol='circle',
                    line=dict(
                        color='white',
                        width=1
                    )
                ),
                customdata=device_data["hover_text"],
                hovertemplate="%{customdata}<extra></extra>"
            ))

        # Y축 텍스트를 HTML로 색상 지정
        colored_labels = [
            f'<span style="color: #28a745">정상</span>',  # 초록색
            f'<span style="color: #ffc107">관심</span>',  # 노란색
            f'<span style="color: #fd7e14">경고</span>',  # 주황색
            f'<span style="color: #dc3545">위험</span>'   # 빨간색
        ]

        # 레이아웃 설정
        fig.update_layout(
            plot_bgcolor='white',
            paper_bgcolor='white',
            height=300,
            yaxis=dict(
                ticktext=colored_labels,
                tickvals=[0, 1, 2, 3],
                title="장비 상태",
                gridcolor='lightgray',
                zeroline=False,
                title_font=dict(size=14),
                tickfont=dict(size=12),
                range=[-0.2, 3.2]
            ),
            xaxis=dict(
                title="시간",
                gridcolor='lightgray',
                zeroline=False,
                title_font=dict(size=14),
                tickfont=dict(size=12),
                tickformat="%H:%M",
                nticks=20
            ),
            hovermode="x unified",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                bgcolor='rgba(255, 255, 255, 0.8)',
                bordercolor='lightgray'
            ),
            margin=dict(l=50, r=50, t=80, b=50)
        )

        # 상태별 색상의 구분선 추가
        status_colors = {
            0: "#28a745",  # 정상 - 초록색
            1: "#ffc107",  # 관심 - 노란색
            2: "#fd7e14",  # 경고 - 주황색
            3: "#dc3545"   # 위험 - 빨간색
        }

        # 상태 구분선 추가
        for y_val in [0, 1, 2, 3]:
            fig.add_hline(
                y=y_val,
                line_dash="solid",
                line_color=status_colors[y_val],
                line_width=2,
                opacity=0.3
            )

        st.plotly_chart(fig, use_container_width=True, key="status_time_series")
        
# ✅ OHT 경고 및 위험 장비 (`aggregated_device_status` 기반)
def oht_warning_risk():
    conn = get_db_connection()
    query = """
        SELECT device_id, normal_ratio, caution_ratio, warning_ratio, risk_ratio
        FROM aggregated_device_status
        WHERE device_id LIKE 'OHT%'
        ORDER BY risk_ratio DESC, warning_ratio DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    if df.empty:
        st.warning("⚠️ 현재 경고 및 위험 상태의 OHT 장비가 없습니다.")
    else:
        # ✅ 상태 재분류 (가장 높은 비율을 기준으로 결정)
        def classify_state(row):
            max_ratio = max(row["normal_ratio"], row["caution_ratio"], row["warning_ratio"], row["risk_ratio"])
            if max_ratio == row["risk_ratio"]:  
                return "위험"
            elif max_ratio == row["warning_ratio"]:  
                return "경고"
            elif max_ratio == row["caution_ratio"]:  
                return "관심"
            return "정상"

        df["상태"] = df.apply(classify_state, axis=1)

        # ✅ 테이블 컬럼명 변경 (가독성 향상)
        df = df.rename(columns={
            "device_id": "장비 ID",
            "normal_ratio": "정상 비율",
            "caution_ratio": "관심 비율",
            "warning_ratio": "경고 비율",
            "risk_ratio": "위험 비율"
        })

        # ✅ 경고 및 위험 상태만 필터링
        df_filtered = df[df["상태"].isin(["경고", "위험"])]

        if df_filtered.empty:
            st.warning("⚠️ 현재 경고 및 위험 상태의 OHT 장비가 없습니다.")
        else:
            # ✅ 경고 및 위험 상태 강조 색상 적용
            def color_state(val):
                if val == "경고":
                    return "background-color: #ffc107; color: black;"  # 노란색
                elif val == "위험":
                    return "background-color: #dc3545; color: white;"  # 빨간색
                return ""

            # ✅ Streamlit 스타일 적용한 테이블 표시
            st.dataframe(df_filtered.style.applymap(color_state, subset=["상태"]))

# ✅ 최근 OHT 작업 환경
# ✅ 최근 OHT 작업 환경
def oht_recent_environment():
    st.markdown("""
        <style>
        [data-testid="metric-container"] {
            width: fit-content;
            margin: auto;
        }

        [data-testid="metric-container"] > div {
            width: fit-content;
            margin: auto;
        }

        [data-testid="metric-container"] label {
            font-size: 0.6rem !important;
            color: rgba(0,0,0,0.6);
        }

        [data-testid="metric-container"] div[data-testid="metric-value"] {
            font-size: 0.8rem !important;
        }

        [data-testid="metric-container"] div[data-testid="metric-delta"] {
            font-size: 0.6rem !important;
        }

        [data-testid="stHorizontalBlock"] {
            gap: 0.5rem !important;
        }
        
        .timestamp {
            text-align: right;
            color: #666;
            font-size: 0.8rem !important;
            margin-top: 0.5rem;
            padding-right: 1rem;
        }
        </style>
    """, unsafe_allow_html=True)
    
    conn = get_db_connection()
    query = """
        SELECT 
            timestamp,
            ex_temperature,
            ex_humidity,
            ex_illuminance
        FROM environment_measurements
        ORDER BY timestamp DESC
        LIMIT 1
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if df.empty:
        st.warning("⚠️ 현재 환경 데이터가 없습니다.")
        return
    
    latest_data = df.iloc[0]
    
    try:
        timestamp = pd.to_datetime(latest_data['timestamp'])
        timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
    except:
        timestamp_str = str(latest_data['timestamp'])
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "온도",
            f"{latest_data['ex_temperature']:.1f}°C"
        )
    
    with col2:
        st.metric(
            "습도",
            f"{latest_data['ex_humidity']:.1f}%"
        )
    
    with col3:
        st.metric(
            "조도",
            f"{latest_data['ex_illuminance']:.0f}lx"
        )
    
    st.markdown(
        f"<div class='timestamp'>"
        f"📅 {timestamp_str}"
        f"</div>",
        unsafe_allow_html=True
    )
        
        
# ✅ OHT 온도 변화 
def oht_temperature_change():
   conn = get_db_connection()
   df = pd.read_sql("SELECT timestamp, ex_temperature FROM environment_measurements", conn) 
   
   if df.empty:
       st.warning("⚠️ 현재 OHT 온도 데이터가 없습니다.")
       return
   
   df["timestamp"] = pd.to_datetime(df["timestamp"], errors='coerce')
   df = df.dropna(subset=["timestamp"])
   df["minute"] = df["timestamp"].dt.floor("min")
   df = df.groupby("minute")[["ex_temperature"]].mean().reset_index()
   conn.close()

   NORMAL_TEMP = 25.494680
   CAUTION_TEMP = 25.464758 
   WARNING_TEMP = 25.480036
   DANGER_TEMP = 25.480520

   st.markdown("""
       <style>
       [data-testid="metric-container"] {
           width: fit-content;
           margin: auto;
       }

       [data-testid="metric-container"] > div {
           width: fit-content;
           margin: auto;
       }

       [data-testid="metric-container"] label {
           font-size: 0.6rem !important;
           color: rgba(0,0,0,0.6);
       }

       [data-testid="metric-container"] div[data-testid="metric-value"] {
           font-size: 0.8rem !important;
       }

       [data-testid="metric-container"] div[data-testid="metric-delta"] {
           font-size: 0.6rem !important;
       }

       .st-emotion-cache-p38tq {
           font-size: 1.6rem !important;
           color: rgb(49, 51, 63) !important;
       }

       [data-testid="stHorizontalBlock"] {
           gap: 0.5rem !important;
       }
               
       </style>
   """, unsafe_allow_html=True)
   
   col1, col2, col3 = st.columns(3)
   current_temp = df["ex_temperature"].iloc[-1]
   max_temp = df["ex_temperature"].max()
   min_temp = df["ex_temperature"].min()
   temp_change = current_temp - df['ex_temperature'].iloc[-2] if len(df) > 1 else 0
   
   with col1:
       st.metric("현재 온도", f"{current_temp:.1f}°C", f"{temp_change:.1f}°C", delta_color="inverse")
   with col2:
       st.metric("최고 온도", f"{max_temp:.1f}°C")
   with col3:
       st.metric("최저 온도", f"{min_temp:.1f}°C")

   fig = go.Figure()
   
   def get_temp_status_color(temp):
       if abs(temp - DANGER_TEMP) <= 0.5:
           return '#FF4444'
       elif abs(temp - WARNING_TEMP) <= 0.5:
           return '#FFA726'  
       elif abs(temp - CAUTION_TEMP) <= 0.5:
           return '#FFC107'
       return '#4CAF50'

   fig.add_hline(y=DANGER_TEMP, line_dash="dash", line_color="#FF4444", annotation_text="위험")
   fig.add_hline(y=WARNING_TEMP, line_dash="dash", line_color="#FFA726", annotation_text="경고")
   fig.add_hline(y=CAUTION_TEMP, line_dash="dash", line_color="#FFC107", annotation_text="주의")

   fig.add_trace(go.Scatter(
       x=df["minute"],
       y=df["ex_temperature"],
       mode="lines+markers",
       line=dict(color=get_temp_status_color(current_temp), width=2),
       marker=dict(
           size=4,
           color=df["ex_temperature"].apply(get_temp_status_color)
       ),
       name="온도 변화",
       hovertemplate="<b>시간</b>: %{x|%H:%M}<br>" +
                     "<b>온도</b>: %{y:.1f}°C<br><extra></extra>"
   ))

   fig.update_layout(
       title="OHT 작업현장 온도",
       height=300,
       margin=dict(l=20, r=20, t=40, b=20),
       xaxis=dict(
           title=None,
           gridcolor='rgba(128,128,128,0.1)',
           nticks=10,
           tickformat="%H:%M"
       ),
       yaxis=dict(
           title=None,
           gridcolor='rgba(128,128,128,0.1)',
           range=[min(NORMAL_TEMP - 0.5, df["ex_temperature"].min() - 0.2),
                  max(DANGER_TEMP + 0.5, df["ex_temperature"].max() + 0.2)]
       ),
       plot_bgcolor='white',
       paper_bgcolor='white',
       showlegend=False,
       hovermode="x unified"
   )

   st.plotly_chart(fig, use_container_width=True)

   def get_temp_status_message(temp):
       if abs(temp - DANGER_TEMP) <= 0.5:
           st.error("⚠️ 온도가 매우 위험한 수준입니다")
       elif abs(temp - WARNING_TEMP) <= 0.5:
           st.warning("⚠️ 온도가 높습니다")
       elif abs(temp - CAUTION_TEMP) <= 0.5:
           st.warning("📢 온도가 약간 상승했습니다")
       else:
           st.success("✅ 온도 정상")

   get_temp_status_message(current_temp)
       
# ✅ OHT 습도 변화
def oht_humidity_change():
    conn = get_db_connection()
    df = pd.read_sql("SELECT timestamp, ex_humidity FROM environment_measurements",conn)
    if df.empty:
        st.warning("⚠️ 현재 OHT 온도 데이터가 없습니다.")
    else:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors='coerce')
        # 변환 실패한 값 제거
        df = df.dropna(subset=["timestamp"])
        # 분 단위로 그룹화하여 평균 계산
        df["minute"] = df["timestamp"].dt.floor("min")
        df = df.groupby("minute")[["ex_humidity"]].mean().reset_index()
        conn.close()
       
        # ✅ go.Scatter를 사용하여 평균값을 시각화
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df["minute"],
            y=df["ex_humidity"],
            mode="lines+markers",  # 선과 마커 동시 표시
            marker=dict(size=4, opacity=0.7),
            line=dict(width=2),
            name="평균 습도 변화"
        ))
       
        fig.update_layout(
            title="OHT 작업현장 습도",
            xaxis_title="시간",
            yaxis_title="평균 습도 (%)",
            xaxis=dict(nticks=20, tickformat="%H:%M"),  # ✅ 초 단위로 표시
            hovermode="x unified",
            template="plotly_white"
        )
        st.plotly_chart(fig, use_container_width=True)
       
# ✅ OHT 조도 변화
def oht_illuminance_change():
   conn = get_db_connection()
   df = pd.read_sql("SELECT timestamp, ex_illuminance FROM environment_measurements", conn) 
   
   if df.empty:
       st.warning("⚠️ 현재 OHT 조도 데이터가 없습니다.")
       return
   
   NORMAL_ILLUM = 155.609421
   CAUTION_ILLUM = 155.480179
   WARNING_ILLUM = 155.352264
   DANGER_ILLUM = 155.241562
   
   df["timestamp"] = pd.to_datetime(df["timestamp"], errors='coerce')
   df = df.dropna(subset=["timestamp"])
   df["minute"] = df["timestamp"].dt.floor("min")
   df = df.groupby("minute")[["ex_illuminance"]].mean().reset_index()
   conn.close()

   st.markdown("""
       <style>
       .st-emotion-cache-p38tq {
           font-size: 1.6rem !important;
           color: rgb(49, 51, 63) !important;
       }
       [data-testid="metric-container"] {
           width: fit-content;
           margin: auto;
       }
       [data-testid="metric-container"] > div {
           width: fit-content;
           margin: auto;
       }
       [data-testid="metric-container"] label {
           font-size: 0.6rem !important;
           color: rgba(0,0,0,0.6);
       }
       [data-testid="metric-container"] div[data-testid="metric-value"] {
           font-size: 0.8rem !important;
       }
       [data-testid="metric-container"] div[data-testid="metric-delta"] {
           font-size: 0.6rem !important;
       }
       [data-testid="stHorizontalBlock"] {
           gap: 0.5rem !important;
       }
       </style>
   """, unsafe_allow_html=True)
   
   col1, col2, col3 = st.columns(3)
   current_illum = df["ex_illuminance"].iloc[-1]
   max_illum = df["ex_illuminance"].max()
   min_illum = df["ex_illuminance"].min()
   illum_change = current_illum - df['ex_illuminance'].iloc[-2] if len(df) > 1 else 0
   
   with col1:
       st.metric("현재 조도", f"{current_illum:.1f} lux", f"{illum_change:.1f} lux", delta_color="inverse")
   with col2:
       st.metric("최고 조도", f"{max_illum:.1f} lux")
   with col3:
       st.metric("최저 조도", f"{min_illum:.1f} lux")

   fig = go.Figure()
   
   def get_illum_status_color(illum):
       if abs(illum - DANGER_ILLUM) <= 0.5:
           return '#FF4444'
       elif abs(illum - WARNING_ILLUM) <= 0.5:
           return '#FFA726'  
       elif abs(illum - CAUTION_ILLUM) <= 0.5:
           return '#FFC107'
       return '#4CAF50'

   fig.add_hline(y=DANGER_ILLUM, line_dash="dash", line_color="#FF4444", annotation_text="위험")
   fig.add_hline(y=WARNING_ILLUM, line_dash="dash", line_color="#FFA726", annotation_text="경고")
   fig.add_hline(y=CAUTION_ILLUM, line_dash="dash", line_color="#FFC107", annotation_text="주의")
   
   fig.add_trace(go.Scatter(
       x=df["minute"],
       y=df["ex_illuminance"],
       mode="lines+markers",
       line=dict(color=get_illum_status_color(current_illum), width=2),
       marker=dict(
           size=4,
           color=df["ex_illuminance"].apply(get_illum_status_color)
       ),
       name="조도 변화",
       hovertemplate="<b>시간</b>: %{x|%H:%M}<br>" +
                     "<b>조도</b>: %{y:.1f} lux<br><extra></extra>"
   ))

   fig.update_layout(
       title="OHT 외부 조도",
       height=300,
       margin=dict(l=20, r=20, t=40, b=20),
       xaxis=dict(
           title=None,
           gridcolor='rgba(128,128,128,0.1)',
           nticks=10,
           tickformat="%H:%M"
       ),
       yaxis=dict(
           title=None,
           gridcolor='rgba(128,128,128,0.1)',
           range=[min(NORMAL_ILLUM - 1, df["ex_illuminance"].min() - 0.5),
                  max(DANGER_ILLUM + 1, df["ex_illuminance"].max() + 0.5)]
       ),
       plot_bgcolor='white',
       paper_bgcolor='white',
       showlegend=False,
       hovermode="x unified"
   )

   st.plotly_chart(fig, use_container_width=True)

   def get_illum_status_message(illum):
       if abs(illum - DANGER_ILLUM) <= 0.5:
           st.error("⚠️ 조도가 매우 낮습니다. 즉시 확인이 필요합니다")
       elif abs(illum - WARNING_ILLUM) <= 0.5:
           st.warning("⚠️ 조도가 낮습니다. 점검이 필요합니다")
       elif abs(illum - CAUTION_ILLUM) <= 0.5:
           st.warning("📢 조도가 약간 낮아졌습니다. 모니터링이 필요합니다")
       else:
           st.success("✅ 조도 정상")

   get_illum_status_message(current_illum)


def oht_thermal_monitoring():
   st.markdown("""
       <style>
       .block-container {padding: 0;}
       .status-card {
           padding: 1rem;
           border-radius: 8px;
       }
       .status-badge {
           text-align: center;
           padding: 0.3rem 1rem;
           border-radius: 4px;
           font-weight: 500;
           margin-bottom: 0.8rem;
       }
       .temp-grid {
           display: grid;
           grid-template-columns: repeat(3, 1fr);
           gap: 1rem;
           text-align: center;
       }
       .temp-label {
           color: #858796;
           font-size: 0.8rem;
           margin-bottom: 0.3rem;
       }
       .temp-value {
           font-size: 1.2rem;
           font-weight: 500;
       }
       </style>
   """, unsafe_allow_html=True)
   
   devices = ['OHT17', 'OHT18']
   
   with st.container():
       cols = st.columns(len(devices))
       for idx, device in enumerate(devices):
           with cols[idx]:
               timestamps = pd.date_range(end=pd.Timestamp.now(), periods=60, freq='S')
               base_temp = 45 + np.sin(np.linspace(0, 2*np.pi, 60)) * 3  
               temps = base_temp + np.random.randn(60) * 0.5
               current_temp = temps[-1]
               
               if current_temp < 47:
                   status = "정상"
                   status_color = "#1cc88a"
                   status_bg = "#e6fff0"
               elif current_temp < 60:
                   status = "주의" 
                   status_color = "#f6c23e"
                   status_bg = "#fff8e6"
               elif current_temp < 75:
                   status = "경고"
                   status_color = "#fd7e14"
                   status_bg = "#fff4e6"
               else:
                   status = "위험"
                   status_color = "#e74a3b"
                   status_bg = "#ffe6e6"

               gauge_fig = go.Figure()
               gauge_fig.add_trace(go.Indicator(
                   mode="gauge+number",
                   value=current_temp,
                   number={'suffix': "°C"},
                   domain={'x': [0, 1], 'y': [0, 1]},
                   title={
                       'text': f"<b>{device}</b><br><span style='font-size:12px;color:gray'>현재 온도</span>",
                       'font': {'color': 'black', 'size': 18}
                   },
                   gauge={
                       'axis': {'range': [20, 80], 'tickwidth': 1},
                       'bar': {'color': "lightgray", 'thickness': 0.1},
                       'bgcolor': "white",
                       'steps': [
                           {'range': [20, 47], 'color': "#1cc88a"},
                           {'range': [47, 60], 'color': "#f6c23e"},
                           {'range': [60, 75], 'color': "#fd7e14"},
                           {'range': [75, 80], 'color': "#e74a3b"}
                       ],
                       'threshold': {
                           'line': {'color': status_color, 'width': 4},
                           'thickness': 1,
                           'value': current_temp
                       }
                   }
               ))

               gauge_fig.update_layout(
                   height=150,
                   margin=dict(t=30, b=10, l=30, r=30),
                   paper_bgcolor='rgba(0,0,0,0)'
               )
               
               st.plotly_chart(gauge_fig, use_container_width=True, config={'displayModeBar': False})
               
               line_fig = go.Figure()
               line_fig.add_trace(go.Scatter(
                   x=timestamps,
                   y=temps,
                   mode='lines',
                   line=dict(color=status_color, width=2)
               ))
               
               line_fig.update_layout(
                   title={
                       'text': f"{device} 열화상 센서 온도", 
                       'y':0.9,
                       'x':0.5,
                       'xanchor': 'center',
                       'yanchor': 'top'
                   },
                   height=150,
                   margin=dict(t=40, b=40, l=30, r=30),
                   showlegend=False,
                   paper_bgcolor='rgba(0,0,0,0)',
                   plot_bgcolor='rgba(0,0,0,0)',
                   yaxis=dict(
                       range=[20, 80],
                       showgrid=True,
                       gridcolor='lightgray'
                   ),
                   xaxis=dict(
                       showgrid=True,
                       gridcolor='lightgray'
                   )
               )
               
               st.plotly_chart(line_fig, use_container_width=True, config={'displayModeBar': False})
               
               st.markdown(f"""
                   <div class="status-card">
                       <div class="status-badge" style="background: {status_bg}; color: {status_color};">
                           {status}
                       </div>
                       <div class="temp-grid">
                           <div>
                               <div class="temp-label">평균</div>
                               <div class="temp-value">{np.mean(temps):.1f}°C</div>
                           </div>
                           <div>
                               <div class="temp-label">최고</div>
                               <div class="temp-value" style="color: {status_color}">{np.max(temps):.1f}°C</div>
                           </div>
                           <div>
                               <div class="temp-label">최저</div>
                               <div class="temp-value">{np.min(temps):.1f}°C</div>
                           </div>
                       </div>
                   </div>
               """, unsafe_allow_html=True)

# ✅ 페이지 선택에 따라 실행
if page == "AGV 상태 분포":
    agv_status_distribution()
elif page == "AGV 경고 및 위험 장비":
    agv_warning_risk()
elif page == "시간에 따른 AGV 상태 변화":
    agv_status_time_series()
elif page == "최근 작업 환경":
    recent_environment()
elif page == "AGV 온도 변화":
    agv_temperature_change()
elif page == "AGV 습도 변화":
    agv_humidity_change()
elif page == "AGV 조도 변화":
    agv_illuminance_change()
elif page == "AGV 상태 현황":
    agv_device_status()
elif page == "AGV 열화상 모니터링":
    agv_thermal_monitoring()

elif page == "OHT 상태 현황":
    oht_device_status()
elif page == "OHT 상태 분포":
    oht_status_distribution()
elif page == "시간에 따른 OHT 상태 변화":
    oht_status_time_series()
elif page == "OHT 경고 및 위험 장비":
    oht_warning_risk()
elif page == "OHT 최근 작업 환경":
    oht_recent_environment()
elif page == "OHT 온도 변화":
    oht_temperature_change()
elif page == "OHT 습도 변화":
    oht_humidity_change()
elif page == "OHT 조도 변화":
    oht_illuminance_change()
elif page == "OHT 열화상 모니터링":
    oht_thermal_monitoring()