import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader
import sqlite3
import pandas as pd
from typing import List, Dict, Any
import time
from datetime import datetime

class DeviceDataPipeline:
   def __init__(self, device='cpu', db_path='sensor_data.db', monitor_interval=30):
       self.device = device
       self.db_path = db_path
       self.monitor_interval = monitor_interval  # 모니터링 간격(초)
       
       # 모델 파라미터
       self.img_dim_h = 120
       self.img_dim_w = 160
       self.patch_size = 16
       self.embed_dim = 128
       self.num_heads = 4
       self.depth = 6
       self.aux_input_dim = 11
       self.num_classes = 4
       
       # 윈도우 파라미터
       self.window_size = 300
       
       # 모델 경로 설정
       self.model_paths = {
           'AGV': 'Parameters/AGV_Best_State_Model.pth',
           'OHT': 'Parameters/OHT_Best_State_Model.pth'
       }

   def load_model(self, device_type: str, model_path: str) -> Any:
       """AGV 또는 OHT 모델 로드"""
       model = ConditionClassifier(
           self.img_dim_w, self.img_dim_h, 
           self.patch_size, self.embed_dim,
           self.num_heads, self.depth,
           self.aux_input_dim, self.num_classes
       )
       model.load_state_dict(torch.load(model_path, map_location=self.device))
       return model.eval()
   
   def load_data(self, table_name: str) -> pd.DataFrame:
       """SQLite에서 데이터 로드"""
       connection = sqlite3.connect(self.db_path)
       query = f"SELECT * FROM {table_name}"
       df = pd.read_sql(query, connection)
       connection.close()
       return df
   
   def get_current_state(self, dataframe: pd.DataFrame) -> pd.DataFrame:
       """현재 상태를 위한 최근 데이터 추출"""
       return dataframe.tail(self.window_size)

   def classify_risk(self, events: torch.Tensor, device_type: str) -> str:
       """위험도 분류"""
       risk_count = (events == 3).sum().item()
       warning_count = (events == 2).sum().item()
       caution_count = (events == 1).sum().item()
       
       if device_type == 'OHT':
           thresholds = {'risk': 15, 'warning': 50, 'caution': 70}
       else:  # AGV
           thresholds = {'risk': 20, 'warning': 60, 'caution': 80}
       
       if risk_count >= thresholds['risk']:
           return "위험"
       elif warning_count >= thresholds['warning']:
           return "경고"
       elif caution_count >= thresholds['caution']:
           return "주의"
       return "정상"

   def process_windows(self, windows: List[pd.DataFrame], model: Any, device_type: str) -> List[str]:
       """윈도우 처리 및 예측"""
       predictions = []
       for idx, window in enumerate(windows):
           dataset = MultimodalTestDataset(window)
           dataloader = DataLoader(dataset, batch_size=self.window_size)
           dataloader = iter(dataloader)
           images, sensors = next(dataloader)
           
           prediction = torch.argmax(F.softmax(model(images, sensors), dim=1), dim=1)
           pred_result = self.classify_risk(prediction, device_type)
           predictions.append(pred_result)
           print(f"Window {idx+1}: {pred_result}")
       return predictions

   def monitor_device(self, device_id: str):
       """실시간 디바이스 상태 모니터링"""
       device_type = 'OHT' if 'oht' in device_id.lower() else 'AGV'
       device_number = ''.join(filter(str.isdigit, device_id))
       table_name = f"{device_type.lower()}{device_number}_table"
       
       # 모델 로드
       model_path = self.model_paths[device_type]
       model = self.load_model(device_type, model_path)
       
       print(f"\n{device_id} 실시간 모니터링 시작...")
       print("=" * 50)
       
       try:
           while True:
               # 현재 시간
               current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
               
               # 최신 데이터 로드
               device_data = self.load_data(table_name)
               current_window = self.get_current_state(device_data)
               
               # 상태 예측
               dataset = MultimodalTestDataset(current_window)
               dataloader = DataLoader(dataset, batch_size=self.window_size)
               images, sensors = next(iter(dataloader))
               
               prediction = torch.argmax(F.softmax(model(images, sensors), dim=1), dim=1)
               current_state = self.classify_risk(prediction, device_type)
               
               # 상태 출력
               print(f"\r[{current_time}] {device_id} 현재 상태: {current_state}", end='')
               
               # 위험 상태일 경우 경고 메시지 출력
               if current_state in ["위험", "경고"]:
                   print(f"\n⚠️ 경고: {device_id}가 {current_state} 상태입니다!")
               
               # 대기
               time.sleep(self.monitor_interval)
               
       except KeyboardInterrupt:
           print("\n\n모니터링 종료")
           
   def analyze_device_full(self, device_id: str):
       """전체 데이터에 대한 디바이스 분석"""
       device_type = 'OHT' if 'oht' in device_id.lower() else 'AGV'
       device_number = ''.join(filter(str.isdigit, device_id))
       table_name = f"{device_type.lower()}{device_number}_table"
       
       print(f"\n{device_id} 전체 데이터 분석 시작...")
       
       # 모델 로드
       model_path = self.model_paths[device_type]
       model = self.load_model(device_type, model_path)
       
       # 데이터 로드
       device_data = self.load_data(table_name)
       total_records = len(device_data)
       
       # 데이터를 window_size 크기의 청크로 나누기
       chunks = []
       for i in range(0, total_records, self.window_size):
           chunk = device_data.iloc[i:i + self.window_size]
           if len(chunk) == self.window_size:  # 완전한 청크만 사용
               chunks.append(chunk)
       
       total_predictions = []
       total_chunks = len(chunks)
       
       print(f"총 {total_chunks}개 데이터 청크 분석 중...")
       
       for i, chunk in enumerate(chunks, 1):
           dataset = MultimodalTestDataset(chunk)
           dataloader = DataLoader(dataset, batch_size=self.window_size)
           images, sensors = next(iter(dataloader))
           
           prediction = torch.argmax(F.softmax(model(images, sensors), dim=1), dim=1)
           current_state = self.classify_risk(prediction, device_type)
           total_predictions.append(current_state)
           
           print(f"\r진행률: {i}/{total_chunks} ({(i/total_chunks)*100:.1f}%) - 현재 상태: {current_state}", end='')
       
       print("\n\n분석 완료!")
       print("\n전체 상태 통계:")
       print(f"총 분석 구간: {len(total_predictions)}")
       print(f"정상 상태: {total_predictions.count('정상')}회 ({total_predictions.count('정상')/len(total_predictions)*100:.1f}%)")
       print(f"주의 상태: {total_predictions.count('주의')}회 ({total_predictions.count('주의')/len(total_predictions)*100:.1f}%)")
       print(f"경고 상태: {total_predictions.count('경고')}회 ({total_predictions.count('경고')/len(total_predictions)*100:.1f}%)")
       print(f"위험 상태: {total_predictions.count('위험')}회 ({total_predictions.count('위험')/len(total_predictions)*100:.1f}%)")
       
       return {
           "device_id": device_id,
           "total_chunks": total_chunks,
           "predictions": total_predictions,
           "stats": {
               "normal": total_predictions.count('정상'),
               "caution": total_predictions.count('주의'),
               "warning": total_predictions.count('경고'),
               "danger": total_predictions.count('위험')
           }
       }

# 사용 예시
if __name__ == "__main__":
   pipeline = DeviceDataPipeline(monitor_interval=30)  # 30초마다 상태 업데이트
   
   # 실시간 모니터링
   pipeline.monitor_device('OHT12')
   
   # 전체 데이터 분석
   #results = pipeline.analyze_device_full('OHT12')