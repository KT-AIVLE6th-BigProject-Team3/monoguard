import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import json
import plotly.graph_objects as go


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

        # 디버깅을 위한 데이터 출력 (선택사항)
        with st.expander("🔍 상세 데이터 확인"):
            st.dataframe(df)
            st.write("상태별 장비 수:", status_counts.to_dict())


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
        SELECT device_id, aggregation_start AS timestamp, normal_ratio, caution_ratio, warning_ratio, risk_ratio
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

        # ✅ 상태 재분류 (가장 높은 비율을 기준으로 상태 결정)
        def classify_state(row):
            max_ratio = max(row["normal_ratio"], row["caution_ratio"], row["warning_ratio"], row["risk_ratio"])
            if max_ratio == row["risk_ratio"]:  
                return "위험"
            elif max_ratio == row["warning_ratio"]:  
                return "경고"
            elif max_ratio == row["caution_ratio"]:  
                return "관심"
            return "정상"

        df["current_state"] = df.apply(classify_state, axis=1)

        # ✅ 상태를 숫자로 매핑 (정상=0, 관심=1, 경고=2, 위험=3)
        state_mapping = {"정상": 0, "관심": 1, "경고": 2, "위험": 3}
        df["state_numeric"] = df["current_state"].map(state_mapping)

        # ✅ 시간에 따른 상태 변화 라인 차트 생성
        fig = px.line(
            df, 
            x="timestamp", 
            y="state_numeric", 
            color="device_id", 
            markers=True,
            labels={"state_numeric": "장비 상태 (0:정상, 1:관심, 2:경고, 3:위험)", "timestamp": "시간"}
        )

        st.plotly_chart(fig, use_container_width=True, key="status_time_series")

# ✅ 최근 AGV 작업 환경
def recent_environment():
    st.markdown("""
        <style>
        [data-testid="stMetricValue"] > div { font-size: 1rem !important; }
        [data-testid="stMetricLabel"] { font-size: 0.6rem !important; }
        [data-testid="stMetricDelta"] > div { font-size: 0.6rem !important; }
        .st-emotion-cache-1ibsh2c { padding: 0rem 0rem 0rem }
        .st-emotion-cache-1104ytp h3 { 
            font-size: 0.8rem; 
            padding: 0.2rem 0px 0.4rem; 
            margin-bottom: 0.4rem; 
        }
        div[data-testid="metric-container"] { gap: 0.2rem; }
        </style>
    """, unsafe_allow_html=True)

    conn = get_db_connection()
    query = """
        SELECT 
            timestamp,
            LAG(ex_temperature) OVER (ORDER BY timestamp) as prev_temp,
            LAG(ex_humidity) OVER (ORDER BY timestamp) as prev_humid,
            LAG(ex_illuminance) OVER (ORDER BY timestamp) as prev_illum,
            ex_temperature,
            ex_humidity,
            ex_illuminance
        FROM environment_measurements
        ORDER BY timestamp DESC
        LIMIT 2
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    if df.empty:
        st.warning("⚠️ 현재 환경 데이터가 없습니다.")
        return

    df['timestamp'] = pd.to_datetime(df['timestamp'])
    latest_data = df.iloc[0]
    
    def get_change(current, previous):
        if previous is None or current == previous:
            return None
        change_pct = ((current - previous) / previous) * 100
        return f"{'+' if change_pct > 0 else ''}{change_pct:.1f}%"

    metrics = {
        '온도': (latest_data['ex_temperature'], get_change(latest_data['ex_temperature'], latest_data['prev_temp']), '°C'),
        '습도': (latest_data['ex_humidity'], get_change(latest_data['ex_humidity'], latest_data['prev_humid']), '%'),
        '조도': (latest_data['ex_illuminance'], get_change(latest_data['ex_illuminance'], latest_data['prev_illum']), 'lux')
    }

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            label="온도",
            value=f"{metrics['온도'][0]:.1f}°C",
            delta=metrics['온도'][1]
        )
    with col2:
        st.metric(
            label="습도",
            value=f"{metrics['습도'][0]:.1f}%",
            delta=metrics['습도'][1]
        )
    with col3:
        st.metric(
            label="조도",
            value=f"{metrics['조도'][0]:.0f}lx",
            delta=metrics['조도'][1]
        )

    # 타임스탬프를 아래에 배치
    st.markdown(
        f"<div style='text-align: left; color: #666; font-size: 0.6rem; margin-top: -0.5rem;'>"
        f"📅 {latest_data['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}"
        f"</div>",
        unsafe_allow_html=True
    )
        
        
# ✅ AGV 온도 변화 
def agv_temperature_change():
   
    conn = get_db_connection()
    df = pd.read_sql("SELECT timestamp, ex_temperature FROM environment_measurements", conn)
    if df.empty:
        st.warning("⚠️ 현재 AGV 온도 데이터가 없습니다.")
    else:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors='coerce')
        # 변환 실패한 값 제거
        df = df.dropna(subset=["timestamp"])
        # 분 단위로 그룹화하여 평균 계산
        df["minute"] = df["timestamp"].dt.floor("min")
        df = df.groupby("minute")[["ex_temperature"]].mean().reset_index()
        conn.close()
        # ✅ X축 시간 표시 간격 조정 (너무 많은 시간값을 표시하지 않도록)
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df["minute"],
            y=df["ex_temperature"],
            mode="lines+markers",  # 선과 마커 동시 표시
            marker=dict(size=4, opacity=0.7),
            line=dict(width=2),
            name="평균 온도 변화"
        ))
       
        fig.update_layout(
            title="AGV 외부 온도 변화 (분 단위)",
            xaxis_title="시간",
            yaxis_title="평균 온도 (°C)",
            xaxis=dict(nticks=20, tickformat="%H:%M"),  # ✅ 초 단위로 표시
            hovermode="x unified",
            template="plotly_white"
        )
        st.plotly_chart(fig, use_container_width=True)
       
# ✅ AGV 습도 변화 
def agv_humidity_change():
    conn = get_db_connection()
    df = pd.read_sql("SELECT timestamp, ex_humidity FROM environment_measurements",conn)
    if df.empty:
        st.warning("⚠️ 현재 AGV 온도 데이터가 없습니다.")
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
            title="AGV 외부 습도 변화 (분 단위)",
            xaxis_title="시간",
            yaxis_title="평균 습도 (%)",
            xaxis=dict(nticks=20, tickformat="%H:%M"),  # ✅ 초 단위로 표시
            hovermode="x unified",
            template="plotly_white"
        )
        st.plotly_chart(fig, use_container_width=True)
       
# ✅ AGV 조도 변화 
def agv_illuminance_change():
    conn = get_db_connection()
    df = pd.read_sql("SELECT timestamp, ex_illuminance FROM environment_measurements",conn)
    conn.close()
 
    if df.empty:
        st.warning("⚠️ 현재 AGV 조도 데이터가 없습니다.")
    else:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors='coerce')
        # 변환 실패한 값 제거
        df = df.dropna(subset=["timestamp"])
        # 분 단위로 그룹화하여 평균 계산
        df["minute"] = df["timestamp"].dt.floor("min")
        df = df.groupby("minute")[["ex_illuminance"]].mean().reset_index()
        conn.close()
 
        # ✅ X축 시간 표시 간격 조정
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df["minute"],
            y=df["ex_illuminance"],
            mode="lines+markers",  # 선과 마커 동시 표시
            marker=dict(size=4, opacity=0.7),
            line=dict(width=2),
            name="평균 조도 변화"
        ))
       
        fig.update_layout(
            title="AGV 외부 조도 변화 (분 단위)",
            xaxis_title="시간",
            yaxis_title="평균 조도 (lux)",
            xaxis=dict(nticks=20, tickformat="%H:%M"),  # ✅ 초 단위로 표시
            hovermode="x unified",
            template="plotly_white"
        )
        st.plotly_chart(fig, use_container_width=True)

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
        SELECT device_id, aggregation_start AS timestamp, normal_ratio, caution_ratio, warning_ratio, risk_ratio
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

        # ✅ 상태 재분류 (가장 높은 비율을 기준으로 상태 결정)
        def classify_state(row):
            max_ratio = max(row["normal_ratio"], row["caution_ratio"], row["warning_ratio"], row["risk_ratio"])
            if max_ratio == row["risk_ratio"]:  
                return "위험"
            elif max_ratio == row["warning_ratio"]:  
                return "경고"
            elif max_ratio == row["caution_ratio"]:  
                return "관심"
            return "정상"

        df["current_state"] = df.apply(classify_state, axis=1)

        # ✅ 상태를 숫자로 매핑 (정상=0, 관심=1, 경고=2, 위험=3)
        state_mapping = {"정상": 0, "관심": 1, "경고": 2, "위험": 3}
        df["state_numeric"] = df["current_state"].map(state_mapping)

        # ✅ 시간에 따른 상태 변화 라인 차트 생성
        fig = px.line(
            df, 
            x="timestamp", 
            y="state_numeric", 
            color="device_id", 
            markers=True,
            labels={"state_numeric": "장비 상태 (0:정상, 1:관심, 2:경고, 3:위험)", "timestamp": "시간"}
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
def oht_recent_environment():
    # 페이지 스타일 설정
    st.markdown("""
        <style>
        [data-testid="stMetricValue"] > div { font-size: 2rem !important; }
        .st-emotion-cache-1ibsh2c { padding: 0rem 0rem 0rem }
        .st-emotion-cache-1104ytp h3 { 
            font-size: 1.2rem; 
            padding: 0.5rem 0px 1rem; 
            color: #2c3e50; 
            border-bottom: 2px solid #eaeaea; 
            margin-bottom: 1rem; 
        }
        </style>
    """, unsafe_allow_html=True)

    conn = get_db_connection()
    query = """
        SELECT 
            timestamp,
            LAG(ex_temperature) OVER (ORDER BY timestamp) as prev_temp,
            LAG(ex_humidity) OVER (ORDER BY timestamp) as prev_humid,
            LAG(ex_illuminance) OVER (ORDER BY timestamp) as prev_illum,
            ex_temperature,
            ex_humidity,
            ex_illuminance
        FROM environment_measurements
        ORDER BY timestamp DESC
        LIMIT 2
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    if df.empty:
        st.warning("⚠️ 현재 환경 데이터가 없습니다.")
        return

    latest_data = df.iloc[0]
    
    # 변화율 계산 함수
    def get_change(current, previous):
        if previous is None or current == previous:
            return None
        change_pct = ((current - previous) / previous) * 100
        return f"{'+' if change_pct > 0 else ''}{change_pct:.1f}%"

    # 메트릭 데이터 준비
    metrics = {
        '온도': (latest_data['ex_temperature'], get_change(latest_data['ex_temperature'], latest_data['prev_temp']), '°C'),
        '습도': (latest_data['ex_humidity'], get_change(latest_data['ex_humidity'], latest_data['prev_humid']), '%'),
        '조도': (latest_data['ex_illuminance'], get_change(latest_data['ex_illuminance'], latest_data['prev_illum']), 'lux')
    }

    # 메트릭 표시
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            label="온도",
            value=f"{metrics['온도'][0]:.1f}°C",
            delta=metrics['온도'][1]
        )
    with col2:
        st.metric(
            label="습도",
            value=f"{metrics['습도'][0]:.1f}%",
            delta=metrics['습도'][1]
        )
    with col3:
        st.metric(
            label="조도",
            value=f"{metrics['조도'][0]:.0f} lux",
            delta=metrics['조도'][1]
        )

    # 타임스탬프 표시
    st.markdown(
        f"<div style='text-align: right; color: #666; font-size: 0.8rem;'>"
        f"📅 최종 업데이트: {latest_data['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}"
        f"</div>",
        unsafe_allow_html=True
    )
        
        
# ✅ OHT 온도 변화 
def oht_temperature_change():
   
    conn = get_db_connection()
    df = pd.read_sql("SELECT timestamp, ex_temperature FROM environment_measurements", conn)
    if df.empty:
        st.warning("⚠️ 현재 OHT 온도 데이터가 없습니다.")
    else:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors='coerce')
        # 변환 실패한 값 제거
        df = df.dropna(subset=["timestamp"])
        # 분 단위로 그룹화하여 평균 계산
        df["minute"] = df["timestamp"].dt.floor("min")
        df = df.groupby("minute")[["ex_temperature"]].mean().reset_index()
        conn.close()
        # ✅ X축 시간 표시 간격 조정 (너무 많은 시간값을 표시하지 않도록)
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df["minute"],
            y=df["ex_temperature"],
            mode="lines+markers",  # 선과 마커 동시 표시
            marker=dict(size=4, opacity=0.7),
            line=dict(width=2),
            name="평균 온도 변화"
        ))
       
        fig.update_layout(
            title="OHT 외부 온도 변화 (분 단위)",
            xaxis_title="시간",
            yaxis_title="평균 온도 (°C)",
            xaxis=dict(nticks=20, tickformat="%H:%M"),  # ✅ 초 단위로 표시
            hovermode="x unified",
            template="plotly_white"
        )
        st.plotly_chart(fig, use_container_width=True)
       
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
            title="OHT 외부 습도 변화 (분 단위)",
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
    df = pd.read_sql("SELECT timestamp, ex_illuminance FROM environment_measurements",conn)
    conn.close()
 
    if df.empty:
        st.warning("⚠️ 현재 OHT 조도 데이터가 없습니다.")
    else:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors='coerce')
        # 변환 실패한 값 제거
        df = df.dropna(subset=["timestamp"])
        # 분 단위로 그룹화하여 평균 계산
        df["minute"] = df["timestamp"].dt.floor("min")
        df = df.groupby("minute")[["ex_illuminance"]].mean().reset_index()
        conn.close()
 
        # ✅ X축 시간 표시 간격 조정
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df["minute"],
            y=df["ex_illuminance"],
            mode="lines+markers",  # 선과 마커 동시 표시
            marker=dict(size=4, opacity=0.7),
            line=dict(width=2),
            name="평균 조도 변화"
        ))
       
        fig.update_layout(
            title="OHT 외부 조도 변화 (분 단위)",
            xaxis_title="시간",
            yaxis_title="평균 조도 (lux)",
            xaxis=dict(nticks=20, tickformat="%H:%M"),  # ✅ 초 단위로 표시
            hovermode="x unified",
            template="plotly_white"
        )
        st.plotly_chart(fig, use_container_width=True)


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