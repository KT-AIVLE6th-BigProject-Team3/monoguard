import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
import numpy as np
import matplotlib.pyplot as plt
import requests
from thermal_image_analysis import ThermalImageAnalysis
import time

st.set_page_config(
    page_title="열화상 모니터링",
    layout="wide",
    initial_sidebar_state="collapsed"
)

DEVICE_INFO = {
    'oht17': {'name': 'OHT 17', 'color': '#FF4D4D', 'icon': '🚛'},
    'oht18': {'name': 'OHT 18', 'color': '#4169E1', 'icon': '🚛'},
    'agv17': {'name': 'AGV 17', 'color': '#2E8B57', 'icon': '🚚'},
    'agv18': {'name': 'AGV 18', 'color': '#FFA500', 'icon': '🚚'}
}

st.markdown("""
    <style>
    header {display: none !important;}
    footer {display: none !important;}
    #MainMenu {display: none !important;}
    button[aria-label=""] {
        display: none !important;
    }
    
    .block-container {
        padding: 0rem !important;
    }
    
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
    
    div[data-testid="stMetricValue"] > div {
        font-size: 1rem !important;
        font-weight: 500;
    }
    
    .status-normal { color: #28a745 !important; }
    .status-warning { color: #ffc107 !important; }
    .status-danger { color: #dc3545 !important; }
    
    .thermal-image-container {
        background-color: #f8f9fc;
        border-radius: 6px;
        padding: 0.5rem;
        margin-bottom: 0.5rem;
    }
    
    .stat-card {
        background-color: white;
        border-radius: 6px;
        padding: 0.5rem;
        margin-bottom: 0.5rem;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    
    h5 {
        font-size: 0.9rem !important;
        margin: 0.5rem 0 !important;
    }
    
    [data-testid="stMarkdownContainer"] {
        font-size: 0.8rem !important;
        line-height: 1.2 !important;
    }
    
    [data-testid="stMarkdownContainer"] p {
        margin: 0.3rem 0 !important;
    }

    [data-testid="stAlert"] {
        display: none;
    }
    
    .stats-container {
        padding: 12px;
        background: white;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    .current-state {
        font-size: 1.1rem;
        font-weight: bold;
        text-align: center;
        padding: 8px;
        margin-bottom: 12px;
        border-radius: 4px;
        background: rgba(0,0,0,0.05);
    }
    
    .temp-stats {
        margin-bottom: 16px;
    }
    
    .temp-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 4px 0;
        font-size: 0.85rem;
    }
    
    .temp-value {
        font-weight: 500;
    }
    
    .state-probs {
        background: rgba(0,0,0,0.02);
        padding: 8px;
        border-radius: 4px;
    }
    
    .device-title {
        font-size: 1.3rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 16px;
        color: #333;
    }
    
    .stats-container {
        padding: 12px;
    }
    
    .current-state {
        font-size: 1.1rem;
        font-weight: bold;
        text-align: center;
        padding: 8px;
        margin-bottom: 12px;
    }
    
    .temp-stats {
        margin-bottom: 12px;
    }
    
    .temp-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 4px 0;
        font-size: 0.85rem;
    }
    
    .temp-value {
        font-weight: 500;
    }
    
    .state-probs {
        font-size: 0.8rem;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

def load_thermal_image(bin_path):
    try:
        data = np.load(bin_path)
        return data
    except Exception as e:
        st.error(f"이미지 로드 중 오류 발생: {str(e)}")
        return None

def get_db_connection():
    try:
        return sqlite3.connect('sensor_data.db')
    except Exception as e:
        st.error(f"데이터베이스 연결 오류: {str(e)}")
        return None

def get_thermal_data(device_id):
    try:
        device_type = 'oht' if 'oht' in device_id.lower() else 'agv'
        number = ''.join(filter(str.isdigit, device_id))
        table = f"{device_type}{number}_table"
        
        conn = get_db_connection()
        if conn is None:
            return []
            
        query = f"SELECT filenames FROM {table}"
        df = pd.read_sql(query, conn)
        conn.close()
        return df['filenames'].tolist()
    except Exception as e:
        st.error(f"데이터 조회 중 오류 발생: {str(e)}")
        return []

def aggregated_high_temperature_mean(window):
    try:
        agg = []
        for image in window['filenames']:
            data = np.load(image)
            agg.append(data.max())
        return np.array(agg).mean()
    except Exception as e:
        st.warning(f"온도 평균 계산 중 오류 발생: {str(e)}")
        return None

def display_thermal_image(img, fig_placeholder):
    try:
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.axis(False)
        cax = ax.imshow(img, cmap="inferno")
        cbar = plt.colorbar(cax)
        cbar.ax.tick_params(labelsize=8)
        fig_placeholder.pyplot(fig)
        plt.close()
    except Exception as e:
        st.error(f"이미지 표시 중 오류 발생: {str(e)}")

def display_statistics(img, window, thermal_analyze, stats_placeholder):
    try:
        avg_temp = np.mean(img)
        min_temp = np.min(img)
        max_temp = np.max(img)
        state_prob = thermal_analyze.ProbabiltyOfState(max_temp)
        agg_temp = aggregated_high_temperature_mean(window)
        
        current_state = max(state_prob.items(), key=lambda x: x[1])[0]
        state_colors = {
            '정상': '#4CAF50',
            '관심': '#FF9800',
            '주의': '#FF5722',
            '위험': '#F44336'
        }
        
        device_type = thermal_analyze.device_id.upper()
        
        stats_placeholder.markdown(
            f"""
            <div class="stats-container">
                <div class="current-state" style="color: {state_colors[current_state]}">
                    현재 상태: {current_state}
                </div>
                <div class="temp-stats">
                    <div class="temp-row">
                        <span>평균 온도</span>
                        <span class="temp-value">{avg_temp:.1f}°C</span>
                    </div>
                    <div class="temp-row">
                        <span>최저 온도</span>
                        <span class="temp-value">{min_temp:.1f}°C</span>
                    </div>
                    <div class="temp-row">
                        <span>최고 온도</span>
                        <span class="temp-value">{max_temp:.1f}°C</span>
                    </div>
                    <div class="temp-row">
                        <span>5분 최고온도 평균</span>
                        <span class="temp-value">{agg_temp:.1f}°C</span>
                    </div>
                </div>
                <div class="state-probs">
                    <span style="color: #4CAF50">정상: {state_prob['정상']*100:.1f}%</span> | 
                    <span style="color: #FF9800">관심: {state_prob['관심']*100:.1f}%</span> | 
                    <span style="color: #FF5722">주의: {state_prob['주의']*100:.1f}%</span> | 
                    <span style="color: #F44336">위험: {state_prob['위험']*100:.1f}%</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"통계 표시 중 오류 발생: {str(e)}")

def main():
    query_params = st.experimental_get_query_params()
    selected_device = query_params.get("device", ["agv17"])[0].lower()
    
    if "current_device" not in st.session_state:
        st.session_state.current_device = selected_device
        
    if st.session_state.current_device != selected_device:
        st.session_state.current_device = selected_device
        st.experimental_rerun()
        
    st.experimental_set_query_params(device=selected_device)
    time.sleep(0.1)

    if selected_device not in DEVICE_INFO:
        st.error("올바르지 않은 기기가 선택되었습니다.")
        return

    thermal_files = get_thermal_data(selected_device)
    
    if not thermal_files:
        st.warning("열화상 데이터를 찾을 수 없습니다.")
        return

    thermal_analyze = ThermalImageAnalysis(selected_device)
    
    image_col, stats_col = st.columns([2, 1])
    
    with image_col:
        st.markdown(f"""
            <div class="device-title">
                {selected_device.upper()} 기기 열화상 센서
            </div>
        """, unsafe_allow_html=True)
        image_placeholder = st.empty()
    
    with stats_col:
        stats_placeholder = st.empty()

    df = pd.DataFrame({'filenames': thermal_files})
    window_size = 301
    step_size = 300

    if "is_streaming" not in st.session_state:
        st.session_state.is_streaming = True

    if st.button("스트리밍 중지" if st.session_state.is_streaming else "스트리밍 시작"):
        st.session_state.is_streaming = not st.session_state.is_streaming

    if st.session_state.is_streaming:
        for start in range(0, len(df) - window_size + 1, step_size):
            if not st.session_state.is_streaming:
                break

            try:
                window = df[start:start + window_size]
                bin_path = window['filenames'].iloc[-1]
                img = load_thermal_image(bin_path)
                
                if img is not None:
                    display_thermal_image(img, image_placeholder)
                    display_statistics(img, window, thermal_analyze, stats_placeholder)
                
                time.sleep(0.1)
                
            except Exception as e:
                st.error(f"데이터 처리 중 오류 발생: {str(e)}")
                time.sleep(1)
                continue

            plt.close('all')

if __name__ == "__main__":
    main()