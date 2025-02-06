import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3

# 페이지 설정
st.set_page_config(
    page_title="온도 모니터링",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# NTC 온도 센서 정보
TEMP_SENSORS = {
    'NTC': {'name': 'NTC 온도센서', 'color': '#FF6B6B', 'limit': 50, 'icon': '🌡️'}
}

# 스타일 설정 (기존 스타일 유지)
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
            WHERE sensor_name = 'NTC'
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

def get_temperature_status(temp):
    if temp < 30:
        return 'status-normal'
    elif temp < 45:
        return 'status-warning'
    return 'status-danger'

def main():
    # 데이터 로드
    df = load_data()
    if df is None or df.empty:
        st.warning("데이터가 없습니다")
        return

    # 현재 데이터 분석
    current_temp = df['sensor_value'].iloc[0]
    prev_temp = df['sensor_value'].iloc[1]
    avg_temp = df['sensor_value'].mean()
    min_temp = df['sensor_value'].min()
    max_temp = df['sensor_value'].max()
    
    # 온도 변화율 계산
    temp_change = current_temp - prev_temp
                
    # 메트릭 표시를 위한 컬럼 생성
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "현재 온도",
            f"{current_temp:.1f}°C",
            f"{temp_change:+.1f}°C",
            delta_color="inverse"
        )
    with col2:
        st.metric(
            "평균 온도",
            f"{avg_temp:.1f}°C"
        )
    with col3:
        st.metric(
            "최저 온도",
            f"{min_temp:.1f}°C"
        )
    with col4:
        st.metric(
            "최고 온도",
            f"{max_temp:.1f}°C"
        )

    # 온도 그래프 생성
    fig = px.line(
        df.sort_values('timestamp'),
        x="timestamp",
        y="sensor_value",
        labels={"sensor_value": "온도 (°C)", "timestamp": "시간"}
    )
    
    fig.update_traces(
        line_color=TEMP_SENSORS['NTC']['color'],
        line_width=1.5,
        hovertemplate="시간: %{x}<br>온도: %{y:.1f}°C<extra></extra>"
    )
    
    # 경고 영역 추가
    fig.add_hrect(
        y0=45, y1=100,
        fillcolor="red", opacity=0.1,
        layer="below", line_width=0
    )
    fig.add_hrect(
        y0=30, y1=45,
        fillcolor="yellow", opacity=0.1,
        layer="below", line_width=0
    )
    
    fig.update_layout(
        height=200,
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