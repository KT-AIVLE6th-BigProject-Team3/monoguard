import torch
from torch.utils.data import DataLoader
from datetime import datetime, timedelta
import threading
import time
from app.predict.dbfunc import Database
from app.predict.MultiModal.dataset import MultimodalTestDataset
from app.predict.MultiModal.model import ConditionClassifier
from app.predict.analyzer import ImprovedSensorAnalyzer

class DeviceMonitor:
    def __init__(self):
        self.db = Database()
        self.model_config = {
            "img_dim_h": 120,
            "img_dim_w": 160,
            "patch_size": 16,
            "embed_dim": 256,
            "num_heads": 8,
            "depth": 6,
            "aux_input_dim": 11,
            "num_classes": 4
        }
        self.models = {}
        self.running = True
        self.window_size = 300
        self.step_size = 30
        self.monitoring_interval = 60
        self.monitoring_devices = set()  # 모니터링 중인 장비 추적
        self.monitoring_threads = {}  # Store monitoring threads


    def is_monitoring(self, device_id: str) -> bool:
        """특정 장비의 모니터링 상태 확인"""
        return device_id in self.monitoring_devices

    def load_model(self, device_type):
        """모델 로드"""
        if device_type not in self.models:
            model = ConditionClassifier(**self.model_config)
            path = f'app/predict/Parameters/{device_type}_Best_State_Model.pth'
            model.load_state_dict(torch.load(path, map_location='cpu'))
            self.models[device_type] = model.eval()
            if(model):
                print("model load Successful!")
        return self.models[device_type]

    def check_device_status(self, device_id):
        try:
            self.monitoring_devices.add(device_id)
            self.db.update_device_status(device_id, {'monitoring_in_progress': True})
            
            device_type = 'OHT' if 'oht' in device_id.lower() else 'AGV'
            
            df = self.db.load_device_data(device_type, device_id[-2:])
            if len(df) < self.window_size:
                print(f"Not enough data for device {device_id}")
                return

            analyzer = ImprovedSensorAnalyzer(self.model_config)
            model = self.load_model(device_type)
            current_time = datetime.now()

            for start in range(0, len(df) - self.window_size + 1, self.step_size):
                window = df.iloc[start:start + self.window_size]
                dataset = MultimodalTestDataset(window)
                dataloader = DataLoader(dataset, batch_size=self.window_size)
                images, sensors = next(iter(dataloader))

                with torch.no_grad():
                    predictions = torch.argmax(model(images, sensors), dim=1)

                # 정수로 카운트하여 정확한 비율 계산
                counts = {
                    'normal': (predictions == 0).sum().item(),
                    'caution': (predictions == 1).sum().item(),
                    'warning': (predictions == 2).sum().item(),
                    'risk': (predictions == 3).sum().item()
                }
                
                total = sum(counts.values())
                ratios = {
                    key: round((count / total) * 100, 1) 
                    for key, count in counts.items()
                }

                # 상태 판별 로직 수정
                if device_type == 'AGV':
                    if counts['risk'] >= 20:
                        status = "위험"
                    elif counts['warning'] >= 60:
                        status = "경고"
                    elif counts['caution'] >= 80:
                        status = "주의"
                    else:
                        status = "정상"
                else:  # OHT
                    if counts['risk'] >= 15:
                        status = "위험"
                    elif counts['warning'] >= 50:
                        status = "경고"
                    elif counts['caution'] >= 70:
                        status = "주의"
                    else:
                        status = "정상"

                window_time = current_time + timedelta(seconds=start)
                
                status_data = {
                    'status': status,
                    'start_time': window_time - timedelta(minutes=5),
                    'end_time': window_time,
                    'ratios': ratios
                }
                self.db.update_device_status(device_id, status_data)

                if start + self.window_size >= len(df):
                    self._update_final_window_data(device_id, window, window_time)
                    analysis_result = analyzer.analyze_device_status(device_id, window)
                    analysis_result['current_state'] = status
                    self._save_analysis_result(device_id, window_time, status, analysis_result)
        finally:
            self.monitoring_devices.remove(device_id)
            
    def _update_final_window_data(self, device_id, window, window_time):
        """마지막 윈도우 데이터 업데이트"""
        data_to_insert = window.tail(self.step_size)
        sensor_columns = [col for col in window.columns 
                       if col not in ['device_id', 'timestamp', 'filenames',
                                    'ex_temperature', 'ex_humidity', 'ex_illuminance']]
        
        for idx, row in data_to_insert.iterrows():
            timestamp = window_time + timedelta(seconds=idx)
            # 환경 데이터 업데이트
            self.db.update_environment_data({
                'temperature': float(row['ex_temperature']),
                'humidity': float(row['ex_humidity']),
                'illuminance': float(row['ex_illuminance'])
            })
            
            # 센서 측정값 업데이트
            measurements = [{
                'timestamp': timestamp,
                'sensor_name': sensor,
                'value': float(row[sensor])
            } for sensor in sensor_columns]
            self.db.update_sensor_measurements(device_id, measurements)

    def _save_analysis_result(self, device_id, timestamp, status, analysis_result):
        """분석 결과 저장"""
        window_start = int(timestamp.timestamp())
        window_end = window_start + self.window_size
        
        self.db.update_device_analysis(
            device_id=device_id,
            timestamp=timestamp,
            window_start=window_start,
            window_end=window_end,
            analysis_data={
                'current_state': status,
                'summary': analysis_result['summary'],
                'critical_issues': analysis_result['critical_issues'],
                'warnings': analysis_result['warnings'],
                'recommendations': analysis_result['recommendations'],
                'sensor_details': analysis_result['sensor_details']

            }
        )

    def monitor_device(self, device_id):
        """Monitor individual device"""
        while self.running:
            try:
                print(f"\n[{datetime.now()}] Checking {device_id}")
                self.check_device_status(device_id)
                time.sleep(self.monitoring_interval)
            except Exception as e:
                print(f"Error monitoring {device_id}: {e}")
                time.sleep(30)

    def start_monitoring(self, device_ids):
        """Start monitoring for given device IDs"""
        for device_id in device_ids:
            if device_id not in self.monitoring_threads:
                thread = threading.Thread(
                    target=self.monitor_device,
                    args=(device_id,),
                    daemon=True
                )
                self.monitoring_threads[device_id] = thread
                thread.start()

    def stop_monitoring(self):
        """모니터링 중지"""
        self.running = False