import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3

# 페이지 설정
st.set_page_config(
    page_title="미세먼지 모니터링",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 미세먼지 센서 정보
DUST_SENSORS = {
    'PM10': {'name': 'PM10 (미세먼지)', 'color': '#FF4D4D', 'limit': 100, 'icon': '➊'},
    'PM2_5': {'name': 'PM2.5 (초미세먼지)', 'color': '#4169E1', 'limit': 50, 'icon': '➋'},
    'PM1_0': {'name': 'PM1.0 (극초미세먼지)', 'color': '#2E8B57', 'limit': 25, 'icon': '➌'}
}


# 스타일 설정
st.markdown("""
    <style>
    header {display: none !important;}
    footer {display: none !important;}
    #MainMenu {display: none !important;}
    /* 특정 버튼 숨기기 */
    button[aria-label=""] {
        display: none !important;
    }

    
    /* 컨테이너 패딩 최소화 */
    .block-container {
        padding: 0rem !important;
        max-width: 95% !important;  # 이 줄 추가

    }
    
    /* 탭 스타일링 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        padding: 0.5rem 0.5rem 0 0.5rem;
        border-bottom: 2px solid #e9ecef;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 2.5rem;
        padding: 0 1.5rem;
        font-size: 0.85rem;
        font-weight: 500;
        border-radius: 4px 4px 0 0;
        border: none;
        border-bottom: 2px solid transparent;
        margin-bottom: -2px;
        background-color: transparent;
        color: #666;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        color: #3182ce;
    }
    
    .stTabs button[aria-selected="true"] {
        background-color: transparent !important;
        border-bottom: 2px solid #3182ce !important;
        color: #3182ce !important;
    }

    /* 탭 하이라이트 색상 변경 */
    [data-baseweb="tab-highlight"] {
        background-color: #3182ce !important;
    }
    
    div[data-baseweb="tab-highlight"] {
        background-color: #3182ce !important;
    }

    .st-c1.st-c2.st-c3.st-c4.st-c5.st-c6.st-cb.st-cc.st-cg.st-ch.st-ci {
        background-color: #3182ce !important;
    }
    
    /* 메트릭 스타일링 */
    div[data-testid="stMetricValue"] > div {
        font-size: 1.4rem !important;
        font-weight: 600;
    }
    div[data-testid="stMetricDelta"] > div {
        font-size: 0.7rem !important;
    }
    div[data-testid="stMetricLabel"] > label {
        font-size: 0.8rem !important;
        color: #666;
    }
    
    /* 상태 색상 */
    .status-normal { color: #28a745 !important; }
    .status-warning { color: #ffc107 !important; }
    .status-danger { color: #dc3545 !important; }
    
    /* 그래프 컨테이너 */
    .plot-container {
        margin: 0 !important;
        padding: 0 !important;
        width: 100% !important;  # 이 줄 추가

    }

    /* 탭 컨텐츠 영역 */
    .stTabs [data-baseweb="tab-panel"] {
        padding: 1rem 0.5rem !important;
    }
    </style>
""", unsafe_allow_html=True)

def load_data():
    try:
        conn = sqlite3.connect('sensor_data.db')
        query = """
            SELECT timestamp, sensor_name, sensor_value 
            FROM sensor_measurements
            WHERE sensor_name IN ('PM10', 'PM2_5', 'PM1_0')
            ORDER BY timestamp DESC 
            LIMIT 300
        """
        df = pd.read_sql_query(query, conn)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        conn.close()
        return df
    except Exception as e:
        st.error("⚠️ 데이터 로드 실패")
        return None

def get_status_color(value, sensor_type):
    limit = DUST_SENSORS[sensor_type]['limit']
    if value <= limit * 0.5:
        return 'status-normal'
    elif value <= limit:
        return 'status-warning'
    return 'status-danger'

def main():
    # 데이터 로드
    df = load_data()
    if df is None or df.empty:
        st.warning("데이터가 없습니다")
        return

    # 탭 생성
    tab1, tab2, tab3 = st.tabs([
        f"{DUST_SENSORS['PM10']['icon']} PM10",
        f"{DUST_SENSORS['PM2_5']['icon']} PM2.5",
        f"{DUST_SENSORS['PM1_0']['icon']} PM1.0"
    ])

    # 각 탭에 대한 컨텐츠
    tabs = {"PM10": tab1, "PM2_5": tab2, "PM1_0": tab3}
    
    for sensor_type, tab in tabs.items():
        with tab:
            sensor_data = df[df['sensor_name'] == sensor_type].copy()
            if not sensor_data.empty:
                # 주요 지표 계산
                current_value = sensor_data['sensor_value'].iloc[0]
                prev_value = sensor_data['sensor_value'].iloc[1]
                avg_value = sensor_data['sensor_value'].mean()
                
                # 변화율 계산
                change_rate = ((current_value - prev_value) / prev_value * 100) if prev_value != 0 else 0
                
                # 메트릭 표시
                cols = st.columns(3)
                with cols[0]:
                    st.metric(
                        "현재 농도",
                        f"{current_value:.1f} µg/m³",
                        f"{change_rate:+.1f}%",
                        delta_color="inverse"
                    )
                with cols[1]:
                    st.metric(
                        "평균 농도",
                        f"{avg_value:.1f} µg/m³"
                    )


                # 그래프 생성
                fig = px.line(
                    sensor_data.sort_values('timestamp'),
                    x="timestamp",
                    y="sensor_value",
                    labels={"sensor_value": "농도 (µg/m³)", "timestamp": "시간"}
                )
                
                fig.update_traces(
                    line_color=DUST_SENSORS[sensor_type]['color'],
                    line_width=1.5,
                    hovertemplate="시간: %{x}<br>농도: %{y:.1f} µg/m³<extra></extra>"
                )
                
                fig.update_layout(
                    height=150,
                    margin=dict(l=0, r=0, t=0, b=0),
                    showlegend=False,
                    xaxis=dict(
                        showgrid=False,
                        showline=True,
                        linewidth=1,
                        linecolor='#e0e0e0',
                        tickformat='%H:%M'
                    ),
                    yaxis=dict(
                        showgrid=True,
                        gridwidth=1,
                        gridcolor='#f0f0f0',
                        showline=True,
                        linewidth=1,
                        linecolor='#e0e0e0'
                    ),
                    plot_bgcolor='white'
                )
                
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

if __name__ == "__main__":
    main()