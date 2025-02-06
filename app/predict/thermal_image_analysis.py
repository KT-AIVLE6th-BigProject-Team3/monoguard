import numpy as np
from typing import Dict
import pandas as pd
import sqlite3
from scipy.stats import norm

class ThermalImageAnalysis():
    def __init__(self,device_id='oht17'):
        self.device_id = device_id # 초기 oht17
        self.device_type = 'oht' if 'oht' in self.device_id.lower() else 'agv'
        self.number = ''.join(filter(str.isdigit, self.device_id))
        self.table = f"{self.device_type}{self.number}_table"
        
    def get_db_connect(self):
        return sqlite3.connect('sensor_data.db')
    
    def get_thermal_data_path(self):
        conn = self.get_db_connect()
        query = f"SELECT filenames FROM {self.table}"
        df = pd.read_sql(query, conn)
        # Close the connection
        conn.close()
        return df
    
    def SlidingWindows(self,step_size=30):
        df = self.get_thermal_data_path()
        # 슬라이딩 윈도우 설정
        window_size = 301  # 한 번에 가져올 크기
        step_size = step_size     # 이동 간격
        windows = []       # 결과를 저장할 리스트
        for start in range(0, len(df) - window_size + 1, step_size):
            window = df[start:start + window_size]  # 300개씩 추출
            windows.append(window)
        return windows
    
    def GetHighTemperatureMeanFromEachWindow(self,step_size=30):
        windows = self.SlidingWindows(step_size)
        # 센서별 상세 분석
        temperature_information = {}
        for idx, window in enumerate(windows):
            window_high_temp = []
            for thermal_image_path in window['filenames']:
                thermal_data = np.load(thermal_image_path)
                window_high_temp.append(thermal_data.max())
            temperature_information[f'Next Window {idx+1}'] = np.array(window_high_temp).mean()
        return temperature_information
        
    def GetHighTemperatureFromAll(self):
        df = self.get_thermal_data_path()
        hightemperature_from_all = []
        for thermal_data in df['filenames']:
            hightemperature_from_all.append(np.load(thermal_data).max())
        return hightemperature_from_all
    
    def ProbabiltyOfState(self,X):
        """주어진 온도가 어떤 상태일 확률을 구해줍니다."""
        states = {
            "정상": {"mu": 46.98520280255504, "sigma": 3.2815089524680134},
            "관심": {"mu": 59.23616774671805, "sigma": 7.6665114195977155},
            "주의": {"mu": 75.2383346324511, "sigma": 9.630514908446683},
            "위험": {"mu": 89.39042362012988, "sigma": 9.063610739121764},
        } # 기기의 상태에 대한 확률을 알려면 정상 범위에서의 고온의 평균, 관심 범위에서의 고온의 평균, 주의 범위에서의 고온의 평균, 위험 범위에서의 고온의 평균을 알아야합니다.

        # 사전 확률 (P(S)), 없으면 균등 분포로 가정
        P_S = {state: 1 / len(states) for state in states}  # 균등 분포 (각 상태가 동일한 확률)

        # 가능도 (Likelihood) P(x | S) 계산
        P_x_given_S = {state: norm.pdf(X, info["mu"], info["sigma"]) for state, info in states.items()}

        # 전체 확률 P(x) 계산
        P_x = sum(P_x_given_S[state] * P_S[state] for state in states)

        # 후험 확률 (Posterior) P(S | x) 계산
        P_S_given_x = {state: (P_x_given_S[state] * P_S[state]) / P_x for state in states}
            
        return P_S_given_x

