import sqlite3
import os
import pandas as pd
from datetime import datetime, timedelta
import json
import joblib

class Database:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.db_path = os.path.join(self.base_dir, 'sensor_data.db')
        self.base_path = './data'

    def get_connection(self):
        #return sqlite3.connect(self.db_path)
        return sqlite3.connect("sensor_data.db") 
    
    def init_tables(self):
        """모든 테이블 초기화 및 초기 데이터 로드"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 필요한 테이블들 생성
        tables = {
            'device_status': '''
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
            ''',
            'aggregated_device_status': '''
                CREATE TABLE IF NOT EXISTS aggregated_device_status (
                    device_id TEXT,
                    status TEXT,
                    aggregation_start DATETIME,
                    aggregation_end DATETIME,
                    normal_ratio REAL,
                    caution_ratio REAL,
                    warning_ratio REAL,
                    risk_ratio REAL,
                    monitoring_in_progress BOOLEAN DEFAULT FALSE,
                    PRIMARY KEY (device_id, aggregation_end)
                )
            ''',
            'device_analysis': '''
                CREATE TABLE IF NOT EXISTS device_analysis (
                    device_id TEXT,
                    timestamp DATETIME,
                    current_state TEXT,
                    summary TEXT,
                    critical_issues TEXT,
                    warnings TEXT,
                    recommendations TEXT,
                    sensor_details TEXT,
                    window_start INTEGER,
                    window_end INTEGER,   
                    PRIMARY KEY (device_id, timestamp)
                )
            ''',
            'sensor_measurements': '''
                CREATE TABLE IF NOT EXISTS sensor_measurements (
                    device_id TEXT,
                    timestamp DATETIME,
                    sensor_name TEXT,
                    sensor_value REAL,
                    PRIMARY KEY (device_id, timestamp, sensor_name)
                )
            ''',
            'environment_measurements': '''
                CREATE TABLE IF NOT EXISTS environment_measurements (
                    timestamp DATETIME,
                    ex_temperature REAL,
                    ex_humidity REAL,
                    ex_illuminance REAL,
                    PRIMARY KEY (timestamp)
                )
            '''
        }
        
        for table_name, create_query in tables.items():
            cursor.execute(create_query)
        
        conn.commit()
        
        # 초기 데이터 로드
        self._load_initial_data()
        conn.close()

    def _load_initial_data(self):
        """초기 데이터 로드"""
        # AGV 데이터 로드
        agv_data = {}
        for i in range(17, 19):
            try:
                with open(f'{self.base_path}/agv{i}_test_df', 'rb') as file:
                    agv_data[i] = joblib.load(file)
            except Exception as e:
                print(f"Error loading AGV{i} data: {e}")

        # OHT 데이터 로드
        oht_data = {}
        for i in range(17, 19):
            try:
                with open(f'{self.base_path}/oht{i}_test_df', 'rb') as file:
                    oht_data[i] = joblib.load(file)
            except Exception as e:
                print(f"Error loading OHT{i} data: {e}")

        # 데이터 전처리
        for dataset in [agv_data, oht_data]:
            for key, df in dataset.items():
                df.columns = [col.replace('.', '_') for col in df.columns]
                if 'filenames' in df.columns:
                    df['filenames'] = df['filenames'].str.replace('\\', '/', regex=False)
                df.drop(columns=['device_id', 'collection_date', 'collection_time', 'cumulative_operating_day'], 
                        inplace=True, errors='ignore')
                
        '''
        # 데이터 전처리
        for dataset in [agv_data, oht_data]:
            for key, df in dataset.items():
                df.columns = [col.replace('.', '_') for col in df.columns]
                if 'filenames' in df.columns:
                    df['filenames'] = '/Users/hwangeunbi/monoguard/app/predict/' + df['filenames'].str.replace('\\', '/', regex=False)
                df.drop(columns=['device_id', 'collection_date', 'collection_time', 'cumulative_operating_day'],
                        inplace=True, errors='ignore')
        '''

        # 데이터베이스에 저장
        conn = self.get_connection()
        for i, df in agv_data.items():
            df.to_sql(f'agv{i}_table', conn, if_exists='replace', index=False)
        for i, df in oht_data.items():
            df.to_sql(f'oht{i}_table', conn, if_exists='replace', index=False)
        conn.close()

    def get_device_status(self, device_id):
        """디바이스 현재 상태 조회"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT status, aggregation_end, normal_ratio, caution_ratio, 
            warning_ratio, risk_ratio, monitoring_in_progress
        FROM aggregated_device_status
        WHERE device_id = ?
        ORDER BY aggregation_end DESC
        LIMIT 1
        ''', (device_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return None
            
        return {
            "current_status": result[0],
            "timestamp": result[1],
            "ratios": {
                "normal": result[2],
                "caution": result[3],
                "warning": result[4],
                "risk": result[5]
            },
            "monitoring_in_progress": bool(result[6]) if result[6] is not None else False
        }

    def get_device_history(self, device_id, limit=10):
        """디바이스 상태 이력 조회"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT aggregation_end, status, normal_ratio, caution_ratio, warning_ratio, risk_ratio
        FROM aggregated_device_status
        WHERE device_id = ?
        ORDER BY aggregation_end DESC
        LIMIT ?
        ''', (device_id, limit))
        
        results = cursor.fetchall()
        conn.close()
        
        return [{
            "timestamp": result[0],
            "status": result[1],
            "ratios": {
                "normal": result[2],
                "caution": result[3],
                "warning": result[4],
                "risk": result[5]
            }
        } for result in results]

    def get_sensor_data(self, device_id, limit=900):
        """센서 데이터 조회"""
        conn = self.get_connection()
        df = pd.read_sql('''
        SELECT timestamp, sensor_name, sensor_value
        FROM sensor_measurements
        WHERE device_id = ?
        ORDER BY timestamp DESC
        LIMIT ?
        ''', conn, params=(device_id, limit))
        conn.close()
        
        sensor_data = {}
        for sensor in df['sensor_name'].unique():
            sensor_df = df[df['sensor_name'] == sensor]
            sensor_data[sensor] = {
                'timestamps': sensor_df['timestamp'].tolist(),
                'values': sensor_df['sensor_value'].tolist()
            }
        return sensor_data

    def get_environment_data(self, limit=900):
        """환경 데이터 조회"""
        conn = self.get_connection()
        df = pd.read_sql(f'''
        SELECT * FROM environment_measurements 
        ORDER BY timestamp DESC 
        LIMIT {limit}
        ''', conn)
        conn.close()
        
        return {
            "timestamps": df['timestamp'].tolist(),
            "ex_temperature": df['ex_temperature'].tolist(),
            "ex_humidity": df['ex_humidity'].tolist(),
            "ex_illuminance": df['ex_illuminance'].tolist()
        }

    def get_device_analysis(self, device_id):
        """디바이스 분석 결과 조회"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
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
            return None
            
        analysis_data = {
            "timestamp": result[0],
            "current_state": result[1],
            "summary": result[2],
            "critical_issues": json.loads(result[3]),
            "warnings": json.loads(result[4]),
            "recommendations": json.loads(result[5]),
            "sensor_details": json.loads(result[6])
        }
        
        cursor.execute('''
        SELECT normal_ratio, caution_ratio, warning_ratio, risk_ratio
        FROM aggregated_device_status
        WHERE device_id = ?
        ORDER BY aggregation_end DESC
        LIMIT 1
        ''', (device_id,))
        
        ratio_result = cursor.fetchone()
        
        if ratio_result:
            analysis_data["state_ratios"] = {
                "normal": ratio_result[0],
                "caution": ratio_result[1],
                "warning": ratio_result[2],
                "risk": ratio_result[3]
            }
            
        conn.close()
        return analysis_data

    def update_device_status(self, device_id: str, status_data: dict):
        """디바이스 상태 업데이트"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            if 'monitoring_in_progress' in status_data:
                # 모니터링 상태만 업데이트
                cursor.execute('''
                UPDATE aggregated_device_status
                SET monitoring_in_progress = ?
                WHERE device_id = ?
                ''', (status_data['monitoring_in_progress'], device_id))
            else:
                # 전체 상태 업데이트
                cursor.execute('''
                INSERT OR REPLACE INTO aggregated_device_status
                (device_id, status, aggregation_start, aggregation_end,
                normal_ratio, caution_ratio, warning_ratio, risk_ratio)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    device_id,
                    status_data['status'],
                    status_data['start_time'],
                    status_data['end_time'],
                    status_data['ratios']['normal'],
                    status_data['ratios']['caution'],
                    status_data['ratios']['warning'],
                    status_data['ratios']['risk']
                ))
            
            conn.commit()
        finally:
            conn.close()

    def update_device_analysis(self, device_id: str, timestamp: datetime, window_start: int, window_end: int, analysis_data: dict):
        """디바이스 분석 결과 업데이트 - 윈도우 정보 포함"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT OR REPLACE INTO device_analysis
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            device_id,
            timestamp,
            analysis_data['current_state'],
            analysis_data['summary'],
            json.dumps(analysis_data['critical_issues'], ensure_ascii=False),
            json.dumps(analysis_data['warnings'], ensure_ascii=False),
            json.dumps(analysis_data['recommendations'], ensure_ascii=False),
            json.dumps(analysis_data['sensor_details'], ensure_ascii=False),
            window_start,
            window_end
        ))
        
        conn.commit()
        conn.close()

    def update_sensor_measurements(self, device_id: str, measurements: list):
        """센서 측정값 업데이트"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        for measurement in measurements:
            cursor.execute('''
            INSERT OR REPLACE INTO sensor_measurements
            VALUES (?, ?, ?, ?)
            ''', (
                device_id,
                measurement['timestamp'],
                measurement['sensor_name'],
                measurement['value']
            ))
        
        conn.commit()
        conn.close()

    def update_environment_data(self, data: dict):
        """환경 데이터 업데이트"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT OR REPLACE INTO environment_measurements
        VALUES (?, ?, ?, ?)
        ''', (
            datetime.now(),
            data['temperature'],
            data['humidity'],
            data['illuminance']
        ))
        
        conn.commit()
        conn.close()
        
    def update_device_status_raw(self, device_id: str, status: str, 
                               normal_ratio: float, caution_ratio: float, 
                               warning_ratio: float, risk_ratio: float):
        """device_status 테이블 업데이트"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT OR REPLACE INTO device_status
        VALUES (?, ?, datetime('now', 'localtime'), ?, ?, ?, ?)
        ''', (
            device_id, 
            status,
            normal_ratio,
            caution_ratio,
            warning_ratio,
            risk_ratio
        ))
        
        conn.commit()
        conn.close()
        
    def get_latest_device_status(self):
        """모든 디바이스의 최신 상태 조회"""
        conn = self.get_connection()
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
    def load_device_data(self, device_type: str, device_number: str):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        table_name = f'{device_type.lower()}{device_number}_table'
        
        try:
            cursor.execute(f'SELECT * FROM {table_name} LIMIT 300')
            data = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            df = pd.DataFrame(data, columns=columns)
            return df
            
        except Exception as e:
            print(f"Error loading data for {device_type}{device_number}: {e}")
            return pd.DataFrame()
        
        finally:
            conn.close()