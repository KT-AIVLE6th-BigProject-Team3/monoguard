from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import pandas as pd
import os, sys, time, threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from warnings import filterwarnings
import joblib
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader
from MultiModal.dataset import MultimodalTestDataset
from MultiModal.model import (
  CrossAttention,
  SoftLabelEncoder, 
  ViTFeatureExtractor,
  ConditionClassifier
)
from aiocache import cached
from app.analyzer import ImprovedSensorAnalyzer
import json
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from weasyprint import HTML
from datetime import datetime
import sqlite3
import json
import os
from io import BytesIO
import tempfile
from fastapi.middleware.cors import CORSMiddleware
filterwarnings(action='ignore')
import os
import torch
import numpy as np
import pandas as pd
from torch.utils.data import Dataset, DataLoader
import torch.nn as nn


base_path = './data'
# 현재 파일의 디렉토리에 고정된 경로 설정
base_dir = os.path.dirname(os.path.abspath(__file__))  # 현재 파일의 절대 경로
db_path = os.path.join(base_dir, 'sensor_data.db')  # sensor_data.db의 고정 경로

def get_db_connection():
  return sqlite3.connect(db_path)

def create_aggregated_status_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS aggregated_device_status (
        device_id TEXT,
        status TEXT,
        aggregation_start DATETIME,
        aggregation_end DATETIME,
        normal_ratio REAL,
        caution_ratio REAL,
        warning_ratio REAL,
        risk_ratio REAL,
        PRIMARY KEY (device_id, aggregation_end)
    )
    ''')
    conn.commit()
    conn.close()
def create_analysis_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS device_analysis (
        device_id TEXT,
        timestamp DATETIME,
        current_state TEXT,
        summary TEXT,
        critical_issues TEXT,  -- JSON array as text
        warnings TEXT,         -- JSON array as text
        recommendations TEXT,  -- JSON array as text
        sensor_details TEXT,   -- JSON object as text
        PRIMARY KEY (device_id, timestamp)
    )
    ''')
    conn.commit()
    conn.close()

def create_monitoring_table():
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute('''
  CREATE TABLE IF NOT EXISTS device_status (
      device_id TEXT,
      status TEXT,
      timestamp DATETIME,
      normal_ratio REAL,
      caution_ratio REAL,
      warning_ratio REAL,
      risk_ratio REAL,
      PRIMARY KEY (device_id, timestamp)
  )
  ''')
  conn.commit()
  conn.close()

def create_sensor_table():
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute('''
  CREATE TABLE IF NOT EXISTS sensor_measurements (
      device_id TEXT,
      timestamp DATETIME,
      sensor_name TEXT,
      sensor_value REAL,
      PRIMARY KEY (device_id, timestamp, sensor_name)
  )
  ''')
  conn.commit()
  conn.close()

def create_environment_table():
   conn = get_db_connection()
   cursor = conn.cursor()
   cursor.execute('''
   CREATE TABLE IF NOT EXISTS environment_measurements (
       timestamp DATETIME,
       ex_temperature REAL,
       ex_humidity REAL,
       ex_illuminance REAL,
       PRIMARY KEY (timestamp)
   )
   ''')
   conn.commit()
   conn.close()

device = 'cpu'
model_config = {
  'img_dim_h': 120, 'img_dim_w': 160,
  'patch_size': 16, 'embed_dim': 128,
  'num_heads': 4, 'depth': 6,
  'aux_input_dim': 11, 'num_classes': 4
}

def insert_environment_data(temp, humid, illum):
   conn = get_db_connection()
   cursor = conn.cursor()
   cursor.execute('''
   INSERT OR REPLACE INTO environment_measurements 
   VALUES (datetime('now', 'localtime'), ?, ?, ?)
   ''', (temp, humid, illum))
   conn.commit()
   conn.close()

def update_device_status(device_id, status, normal_ratio, caution_ratio, warning_ratio, risk_ratio):
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute('''
  INSERT OR REPLACE INTO device_status
  VALUES (?, ?, datetime('now', 'localtime'), ?, ?, ?, ?)
  ''', (device_id, status, normal_ratio, caution_ratio, warning_ratio, risk_ratio))
  conn.commit()
  conn.close()

def insert_sensor_measurements(device_id, window_data, is_first_window=False):
   conn = get_db_connection()
   cursor = conn.cursor()
   
   data_to_insert = window_data if is_first_window else window_data.tail(30)
   # 외부 센서 데이터 제외
   sensor_columns = [col for col in window_data.columns 
                    if col not in ['device_id', 'timestamp', 'filenames', 
                                 'ex_temperature', 'ex_humidity', 'ex_illuminance']]
   
   timestamp = datetime.now()
   for idx, row in data_to_insert.iterrows():
       current_timestamp = timestamp + timedelta(seconds=idx)
       for sensor in sensor_columns:
           cursor.execute('''
           INSERT OR REPLACE INTO sensor_measurements 
           VALUES (?, ?, ?, ?)
           ''', (device_id, current_timestamp, sensor, float(row[sensor])))

       # 환경 데이터 저장
       cursor.execute('''
       INSERT OR REPLACE INTO environment_measurements 
       VALUES (?, ?, ?, ?)
       ''', (current_timestamp, float(row['ex_temperature']), 
             float(row['ex_humidity']), float(row['ex_illuminance'])))
           
   conn.commit()
   conn.close()

def get_latest_status():
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute('''
  SELECT device_id, status, timestamp, normal_ratio, caution_ratio, warning_ratio, risk_ratio
  FROM device_status
  GROUP BY device_id
  HAVING timestamp = MAX(timestamp)
  ''')
  results = cursor.fetchall()
  conn.close()
  return results

def load_model(device_type):
  model = ConditionClassifier(**model_config)
  path = f'Parameters/{device_type}_Best_State_Model.pth'
  model.load_state_dict(torch.load(path, map_location='cpu'))
  return model.eval()

def load_data():
  agv_data = {}
  for i in range(17, 19):
      with open(f'{base_path}/agv{i}_test_df', 'rb') as file:
          agv_data[i] = joblib.load(file)
          
  oht_data = {}
  for i in range(17, 19):
      with open(f'{base_path}/oht{i}_test_df', 'rb') as file:
          oht_data[i] = joblib.load(file)

  for dataset in [agv_data, oht_data]:
      for key, df in dataset.items():
          df.columns = [col.replace('.', '_') for col in df.columns]
          if 'filenames' in df.columns:
              df['filenames'] = df['filenames'].str.replace('\\', '/', regex=False)
          df.drop(columns=['device_id', 'collection_date', 'collection_time', 'cumulative_operating_day'], 
                  inplace=True)
  
  return agv_data, oht_data

def create_and_populate_tables(data_dict, prefix):
  conn = get_db_connection()
  for i, df in data_dict.items():
      table_name = f'{prefix}{i}_table'
      df.to_sql(table_name, conn, if_exists='replace', index=False)
      print(f'{table_name}에 데이터 삽입 완료')
  conn.close()

def check_device_status(device_id):
   conn = get_db_connection()
   cursor = conn.cursor()

   try:
       # 초기 데이터 로드
       device_type = 'oht' if 'oht' in device_id.lower() else 'agv'
       cursor.execute(f'SELECT * FROM {device_type.lower()}{device_id[-2:]}_table LIMIT 300')
       data = cursor.fetchall()
       columns = [description[0] for description in cursor.description]
       df = pd.DataFrame(data, columns=columns)

       if len(df) == 0:
           print(f"No data for device {device_id}")
           return

       window_size = 300
       step_size = 30

       # 센서 분석기 초기화
       analyzer = ImprovedSensorAnalyzer(model_config)

       cursor.execute('BEGIN TRANSACTION')
       try:
           for start in range(0, len(df) - window_size + 1, step_size):
               window = df.iloc[start:start + window_size]
               
               # 모델 예측
               dataset = MultimodalTestDataset(window)
               dataloader = DataLoader(dataset, batch_size=window_size)
               images, sensors = next(iter(dataloader))

               model = load_model(device_type.upper())
               with torch.no_grad():
                   predictions = torch.argmax(model(images, sensors), dim=1)

               # 비율 계산 
               total = len(predictions)
               risk = (predictions == 3).sum().item()
               warning = (predictions == 2).sum().item()
               caution = (predictions == 1).sum().item()
               normal = (predictions == 0).sum().item()

               ratios = [count/total * 100 for count in [normal, caution, warning, risk]]
               normal_ratio, caution_ratio, warning_ratio, risk_ratio = ratios

               # 상태 결정
               if device_type == 'agv':
                   current_status = "위험" if risk_ratio >= 20 else \
                                  "경고" if warning_ratio >= 60 else \
                                  "주의" if caution_ratio >= 80 else "정상"
               else:
                   current_status = "위험" if risk_ratio >= 15 else \
                                  "경고" if warning_ratio >= 50 else \
                                  "주의" if caution_ratio >= 70 else "정상"

               # 현재 시간
               current_time = datetime.now()

               # 상태 저장 
               cursor.execute('''
               INSERT OR REPLACE INTO aggregated_device_status
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)
               ''', (device_id, current_status, current_time - timedelta(minutes=5),
                     current_time, normal_ratio, caution_ratio, warning_ratio, risk_ratio))

               # 마지막 윈도우에서만 센서 데이터와 분석 결과 저장
               if start + window_size >= len(df):
                   # 센서 데이터 저장 (마지막 30개)
                   data_to_insert = window.tail(30)
                   sensor_columns = [col for col in window.columns 
                                   if col not in ['device_id', 'timestamp', 'filenames', 
                                               'ex_temperature', 'ex_humidity', 'ex_illuminance']]
                   
                   for idx, row in data_to_insert.iterrows():
                       current_timestamp = current_time + timedelta(seconds=idx)
                       for sensor in sensor_columns:
                           cursor.execute('''
                           INSERT OR REPLACE INTO sensor_measurements 
                           VALUES (?, ?, ?, ?)
                           ''', (device_id, current_timestamp, sensor, float(row[sensor])))

                       cursor.execute('''
                       INSERT OR REPLACE INTO environment_measurements 
                       VALUES (?, ?, ?, ?)
                       ''', (current_timestamp, float(row['ex_temperature']), 
                            float(row['ex_humidity']), float(row['ex_illuminance'])))
                   
                   # 센서 분석 수행 및 저장
                   analysis_result = analyzer.analyze_device_status(device_id, window)
                   analysis_result['current_state'] = current_status
                   
                   cursor.execute('''
                   INSERT OR REPLACE INTO device_analysis 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                   ''', (
                       device_id,
                       current_time,
                       current_status,
                       analysis_result['summary'],
                       json.dumps(analysis_result.get('critical_issues', []), ensure_ascii=False),
                       json.dumps(analysis_result.get('warnings', []), ensure_ascii=False),
                       json.dumps(analysis_result.get('recommendations', []), ensure_ascii=False),
                       json.dumps(analysis_result.get('sensor_details', {}), ensure_ascii=False)
                   ))

           cursor.execute('COMMIT')
       except Exception as e:
           cursor.execute('ROLLBACK')
           raise e

   except Exception as e:
       print(f"Error in check_device_status for {device_id}: {str(e)}")
   finally:
       conn.close()


def monitor_device(device_id):
    try:
        while True:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"\n[{current_time}] {device_id} 상태 분석 시작")
            check_device_status(device_id)  # 슬라이딩 윈도우 방식으로 상태 체크
            time.sleep(30)  # 슬라이딩 윈도우 이동 간격 (30초)
    except KeyboardInterrupt:
        print(f"Monitoring for {device_id} stopped.")


def monitor_devices(device_ids):
  threads = []
  for device_id in device_ids:
      thread = threading.Thread(target=monitor_device, args=(device_id,))
      thread.daemon = True
      thread.start()
      threads.append(thread)

  try:
      while True:
          print("\n\n====== 기기 상태 모니터링 ======")
          print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]")
          
          latest_status = get_latest_status()
          for device_id, status, timestamp, normal, caution, warning, risk in latest_status:
              print(f"\n{device_id}:")
              print(f"상태: {status}")
              print(f"정상: {normal:.1f}%")
              print(f"주의: {caution:.1f}%")
              print(f"경고: {warning:.1f}%")
              print(f"위험: {risk:.1f}%")
          
          time.sleep(300)
  except KeyboardInterrupt:
      print("\n모니터링을 종료합니다...")

# 데이터베이스 생성
def init_db():
    create_monitoring_table()
    create_analysis_table()
    create_sensor_table()
    create_environment_table()
    create_aggregated_status_table()  # 추가된 함수
    agv_data, oht_data = load_data()
    create_and_populate_tables(agv_data, 'agv')
    create_and_populate_tables(oht_data, 'oht')


# DB 초기화 실행
init_db()

class DeviceStateManager:
    def __init__(self):
        self.models = {}
        self.devices = ['AGV17', 'AGV18', 'OHT17','OHT18']
        self.running = True
        
    def get_model(self, device_type):
        if device_type not in self.models:
            model = ConditionClassifier(**model_config)
            path = f'Parameters/{device_type}_Best_State_Model.pth'
            model.load_state_dict(torch.load(path, map_location='cpu'))
            self.models[device_type] = model.eval()
        return self.models[device_type]

    def check_device_status(self, device_id):
        device_type = 'oht' if 'oht' in device_id.lower() else 'agv'
        model = self.get_model(device_type.upper())
        check_device_status(device_id)  # 기존 함수 호출

    def start_monitoring(self):
        for device_id in self.devices:
            thread = threading.Thread(target=self.monitor_device, args=(device_id,))
            thread.daemon = True
            thread.start()

    def monitor_device(self, device_id):
        while self.running:
            try:
                self.check_device_status(device_id)
                time.sleep(300)
            except Exception as e:
                print(f"Error monitoring {device_id}: {e}")
                time.sleep(30)

state_manager = DeviceStateManager()

app = FastAPI()

app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Welcome to the API"}

@app.on_event("startup")
async def startup_event():
    # 상태 모니터링은 별도로 실행
    threading.Thread(target=state_manager.start_monitoring, daemon=True).start()


@cached(ttl=300)  # 5분 동안 캐시 유지
async def get_cached_device_status(device_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
    SELECT status, timestamp, normal_ratio, caution_ratio, warning_ratio, risk_ratio
    FROM device_status
    WHERE device_id = ?
    ORDER BY timestamp DESC
    LIMIT 1
    ''', (device_id,))

    result = cursor.fetchone()
    conn.close()

    if not result:
        raise HTTPException(status_code=404, detail="Device not found")

    return {
        "current_status": result[0],
        "timestamp": result[1],
        "counts": {
            "normal_count": result[2],
            "caution_count": result[3],
            "warning_count": result[4],
            "risk_count": result[5]
        }
    }

@app.get("/device_status/{device_id}")
async def get_device_status(device_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()

    # 최신 집계 상태 가져오기
    cursor.execute('''
    SELECT status, aggregation_start, aggregation_end, 
           normal_ratio, caution_ratio, warning_ratio, risk_ratio
    FROM aggregated_device_status
    WHERE device_id = ?
    ORDER BY aggregation_end DESC
    LIMIT 1
    ''', (device_id,))

    result = cursor.fetchone()
    conn.close()

    if not result:
        raise HTTPException(status_code=404, detail="Device not found")

    return {
        "current_status": result[0],
        "aggregation_period": {
            "start": result[1],
            "end": result[2]
        },
        "counts": {
            "normal_count": result[3],
            "caution_count": result[4],
            "warning_count": result[5],
            "risk_count": result[6]
        }
    }


@app.get("/device_history/{device_id}")
async def get_device_history(device_id: str):
    conn = get_db_connection()

    df = pd.read_sql(f'''
    SELECT aggregation_end as timestamp, status, 
           normal_ratio, caution_ratio, warning_ratio, risk_ratio
    FROM aggregated_device_status
    WHERE device_id = ?
    ORDER BY aggregation_end DESC
    LIMIT 10
    ''', conn, params=(device_id,))

    conn.close()

    history = []
    for _, row in df.iterrows():
        history.append({
            "timestamp": row["timestamp"],
            "status": row["status"],
            "counts": {
                "normal_count": float(row["normal_ratio"]),  # float로 변환 추가
                "caution_count": float(row["caution_ratio"]),
                "warning_count": float(row["warning_ratio"]),
                "risk_count": float(row["risk_ratio"])
            }
        })

    return history

@app.get("/sensor_data/{device_id}")
async def get_sensor_data(device_id: str):
  conn = get_db_connection()
  
  df = pd.read_sql(f'''
  SELECT timestamp, sensor_name, sensor_value
  FROM sensor_measurements
  WHERE device_id = ?
  ORDER BY timestamp DESC
  LIMIT 900
  ''', conn, params=(device_id,))
  
  conn.close()
  
  sensor_data = {}
  for sensor in df['sensor_name'].unique():
      sensor_df = df[df['sensor_name'] == sensor]
      sensor_data[sensor] = {
          'timestamps': sensor_df['timestamp'].tolist(),
          'values': sensor_df['sensor_value'].tolist()
      }
      
  return sensor_data

@app.get("/environment_data")
async def get_environment_data():
   conn = get_db_connection()
   df = pd.read_sql('''
   SELECT * FROM environment_measurements 
   ORDER BY timestamp DESC 
   LIMIT 900
   ''', conn)
   conn.close()
   
   return {
       "timestamps": df['timestamp'].tolist(),
       "ex_temperature": df['ex_temperature'].tolist(),
       "ex_humidity": df['ex_humidity'].tolist(),
       "ex_illuminance": df['ex_illuminance'].tolist()
   }

@app.get("/analyze_device/{device_id}")
async def analyze_device(device_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 최신 분석 결과 가져오기
        cursor.execute('''
        SELECT timestamp, current_state, summary, critical_issues, 
               warnings, recommendations, sensor_details
        FROM device_analysis
        WHERE device_id = ?
        ORDER BY timestamp DESC
        LIMIT 1
        ''', (device_id,))
        
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        # 상태 비율도 함께 가져오기
        cursor.execute('''
        SELECT normal_ratio, caution_ratio, warning_ratio, risk_ratio
        FROM aggregated_device_status
        WHERE device_id = ?
        ORDER BY aggregation_end DESC
        LIMIT 1
        ''', (device_id,))
        
        ratio_result = cursor.fetchone()
        
        analysis_data = {
            "timestamp": result[0],
            "current_state": result[1],
            "summary": result[2],
            "critical_issues": json.loads(result[3]),
            "warnings": json.loads(result[4]),
            "recommendations": json.loads(result[5]),
            "sensor_details": json.loads(result[6])
        }
        
        if ratio_result:
            analysis_data["state_ratios"] = {
                "normal": ratio_result[0],
                "caution": ratio_result[1],
                "warning": ratio_result[2],
                "risk": ratio_result[3]
            }
        
        return analysis_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
    
def create_html_report(device_id: str) -> str:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 기존 데이터 조회 쿼리들은 유지
        cursor.execute('''
            SELECT status, aggregation_end, normal_ratio, caution_ratio, warning_ratio, risk_ratio
            FROM aggregated_device_status
            WHERE device_id = ?
            ORDER BY aggregation_end DESC
            LIMIT 1
        ''', (device_id,))
        status_result = cursor.fetchone()
        
        # 분석 정보 조회
        cursor.execute('''
            SELECT timestamp, current_state, summary, critical_issues, 
                   warnings, recommendations, sensor_details
            FROM device_analysis
            WHERE device_id = ?
            ORDER BY timestamp DESC
            LIMIT 1
        ''', (device_id,))
        analysis_result = cursor.fetchone()
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ 
                    font-family: 'Malgun Gothic', sans-serif; 
                    margin: 40px; 
                    color: #000;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: 20px;
                }}
                th, td {{
                    border: 1px solid #000;
                    padding: 8px;
                    text-align: center;
                }}
                th {{
                    background-color: #f2f2f2;
                }}
                .title {{
                    text-align: center;
                    font-weight: bold;
                    font-size: 20px;
                    margin-bottom: 20px;
                    border: 1px solid #000;
                    padding: 10px;
                }}
                .section-header {{
                    background-color: #f2f2f2;
                    font-weight: bold;
                }}
                .info-row td:first-child {{
                    width: 20%;
                    background-color: #f2f2f2;
                }}
            </style>
        </head>
        <body>
            <div class="title">설비 이력 카드</div>
            
            <table>
                <tr class="info-row">
                    <td>관리번호</td>
                    <td colspan="2">{device_id}</td>
                    <td>설비명</td>
                    <td colspan="2">{'AGV' if 'AGV' in device_id else 'OHT'}</td>
                </tr>
                <tr class="info-row">
                    <td>담당자</td>
                    <td colspan="2">관리자</td>
                    <td>점검일시</td>
                    <td colspan="2">{status_result[1]}</td>
                </tr>
                <tr class="info-row">
                    <td>현재상태</td>
                    <td colspan="5">{status_result[0]}</td>
                </tr>
            </table>

            <table>
                <tr class="section-header">
                    <td colspan="6">상태 분석</td>
                </tr>
                <tr>
                    <th>정상</th>
                    <th>주의</th>
                    <th>경고</th>
                    <th>위험</th>
                </tr>
                <tr>
                    <td>{status_result[2]:.1f}%</td>
                    <td>{status_result[3]:.1f}%</td>
                    <td>{status_result[4]:.1f}%</td>
                    <td>{status_result[5]:.1f}%</td>
                </tr>
            </table>

            <table>
                <tr class="section-header">
                    <td colspan="4">점검 내용</td>
                </tr>
                <tr>
                    <th>항목</th>
                    <th>현재 상태</th>
                    <th>조치 내용</th>
                    <th>비고</th>
                </tr>
        """
        
        # 중요 이슈들을 테이블 행으로 추가
        issues = json.loads(analysis_result[3])
        warnings = json.loads(analysis_result[4])
        recommendations = json.loads(analysis_result[5])
        
        for issue in issues:
            html_content += f"""
                <tr>
                    <td>중요 이슈</td>
                    <td>{issue}</td>
                    <td>{next((rec for rec in recommendations if any(word in rec.lower() for word in issue.lower().split())), '-')}</td>
                    <td>위험</td>
                </tr>
            """
        
        for warning in warnings:
            html_content += f"""
                <tr>
                    <td>경고사항</td>
                    <td>{warning}</td>
                    <td>{next((rec for rec in recommendations if any(word in rec.lower() for word in warning.lower().split())), '-')}</td>
                    <td>주의</td>
                </tr>
            """
            
        html_content += """
            </table>
        </body>
        </html>
        """
        
        return html_content
        
    finally:
        conn.close()

@app.get("/device_report_pdf/{device_id}")
async def generate_pdf_report(device_id: str):
    try:
        # HTML 보고서 생성
        html_content = create_html_report(device_id)
        
        # 임시 파일로 PDF 생성
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            HTML(string=html_content).write_pdf(tmp.name)
            
            # PDF 파일 응답
            return FileResponse(
                tmp.name,
                media_type='application/pdf',
                filename=f'{device_id}_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
