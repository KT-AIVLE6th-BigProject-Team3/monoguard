import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3

st.set_page_config(page_title="습도 모니터링", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    header {display: none !important;}
    footer {display: none !important;}
    #MainMenu {display: none !important;}
    button[aria-label=""] {
        display: none !important;
    }
    
    .block-container {padding: 0rem !important; max-width: 95% !important;}
    div[data-testid="stMetricValue"] > div {font-size: 1.4rem !important; font-weight: 600;}
    div[data-testid="stMetricDelta"] > div {font-size: 0.7rem !important;}
    div[data-testid="stMetricLabel"] > label {font-size: 0.8rem !important; color: #666;}
    .plot-container {margin: 0 !important; padding: 0 !important; width: 100% !important;}
    </style>
""", unsafe_allow_html=True)

def load_data():
    try:
        conn = sqlite3.connect('sensor_data.db')
        query = """
            SELECT timestamp, ex_humidity 
            FROM environment_measurements
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

def main():
    df = load_data()
    if df is None or df.empty:
        st.warning("데이터가 없습니다")
        return

    current_val = df['ex_humidity'].iloc[0]
    prev_val = df['ex_humidity'].iloc[1]
    avg_val = df['ex_humidity'].mean()
    change_rate = ((current_val - prev_val) / prev_val * 100) if prev_val != 0 else 0
    
    cols = st.columns(2)
    with cols[0]:
        st.metric(
            "현재 습도",
            f"{current_val:.1f} %",
            f"{change_rate:+.1f}%",
            delta_color="inverse"
        )
    with cols[1]:
        st.metric(
            "평균 습도",
            f"{avg_val:.1f} %"
        )

    fig = px.line(
        df.sort_values('timestamp'),
        x="timestamp",
        y="ex_humidity",
        labels={"ex_humidity": "습도 (%)", "timestamp": "시간"}
    )
    
    fig.update_traces(
        line_color="#4169E1",
        line_width=1.5,
        hovertemplate="시간: %{x}<br>습도: %{y:.1f} %<extra></extra>"
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