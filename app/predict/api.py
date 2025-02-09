from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from database import Database
from datetime import datetime
import pandas as pd
import json
import tempfile
from weasyprint import HTML
from aiocache import cached
import torch
from monitor import DeviceMonitor
from analyzer import ImprovedSensorAnalyzer
from MultiModal.dataset import MultimodalTestDataset
from torch.utils.data import DataLoader
import os
import openai
import sqlite3
from typing import List

router = APIRouter()
db = Database()
'''
# 열화상 데이터용 데이터베이스 연결 함수
def get_thermal_db_connection():
    return sqlite3.connect('./sensor_data.db')

def extract_thermal(device_id: str) -> List[str]:
    """열화상 이미지 경로 추출 함수"""
    device_type = 'oht' if 'oht' in device_id.lower() else 'agv'
    number = ''.join(filter(str.isdigit, device_id))
    table = f"{device_type}{number}_table"
    
    conn = get_thermal_db_connection()
    try:
        df = pd.read_sql(f'SELECT filenames FROM {table}', conn)
        return df['filenames'].tolist()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"데이터베이스 조회 중 오류 발생: {str(e)}")
    finally:
        conn.close()

@router.get("/get_thermal_data/{device_id}", response_model=List[str])
async def get_thermal_data(device_id: str):
    """열화상 데이터 조회 엔드포인트"""
    try:
        filenames = extract_thermal(device_id)
        return filenames
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"열화상 데이터 조회 중 오류 발생: {str(e)}")
'''

@router.get("/device_history/{device_id}")
async def get_device_history(device_id: str):
    """디바이스 상태 이력 조회"""
    conn = db.get_connection()
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
                "normal_count": float(row["normal_ratio"]),
                "caution_count": float(row["caution_ratio"]),
                "warning_count": float(row["warning_ratio"]),
                "risk_count": float(row["risk_ratio"])
            }
        })
    return history

@router.get("/sensor_data/{device_id}")
async def get_sensor_data(device_id: str):
    """센서 데이터 조회"""
    conn = db.get_connection()
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

@router.get("/environment_data")
async def get_environment_data():
    """환경 데이터 조회"""
    conn = db.get_connection()
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
    
@router.get("/analyze_device/{device_id}")
async def analyze_device(device_id: str):
    """디바이스 분석 결과 조회"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        # 최신 분석 결과 조회
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
        
        # 상태 비율도 함께 조회
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
        
    finally:
        conn.close()



# 파일에서 API 키 로드 및 환경변수 설정
def load_file(filename):
    """파일에서 내용을 읽어 반환하는 함수"""
    with open(filename, "r", encoding="utf-8") as file:
        return file.read().strip()  # 불필요한 공백 제거

openai_api_key = load_file("api_key.txt")
os.environ["OPENAI_API_KEY"] = openai_api_key
openai.api_key = os.getenv("OPENAI_API_KEY")  # 환경변수에서 가져오기

def generate_conclusion(device_id: str, analysis_result):
    """ChatGPT를 사용하여 분석 결과를 요약하고 결론을 도출"""
    
    # None 체크 및 기본값 설정
    summary = analysis_result[2] if analysis_result[2] else "분석 요약 없음"
    critical_issues = json.loads(analysis_result[3]) if analysis_result[3] else []
    warnings = json.loads(analysis_result[4]) if analysis_result[4] else []
    recommendations = json.loads(analysis_result[5]) if analysis_result[5] else []
    sensor_details = json.loads(analysis_result[6]) if analysis_result[6] else {}

    # 센서별 상태 분석
    critical_sensors = []
    warning_sensors = []
    caution_sensors = []
    
    for sensor_name, details in sensor_details.items():
        if details['status'] == '위험':
            critical_sensors.append(f"{sensor_name}: {details['current_value']:.2f}")
        elif details['status'] == '경고':
            warning_sensors.append(f"{sensor_name}: {details['current_value']:.2f}")
        elif details['status'] == '주의':
            caution_sensors.append(f"{sensor_name}: {details['current_value']:.2f}")

    # ChatGPT 프롬프트 작성
    prompt = f"""
    다음은 장비 {device_id}의 최신 분석 데이터입니다.

    분석 요약: {summary}

    위험 수준 센서: {', '.join(critical_sensors) if critical_sensors else '없음'}
    경고 수준 센서: {', '.join(warning_sensors) if warning_sensors else '없음'}
    주의 수준 센서: {', '.join(caution_sensors) if caution_sensors else '없음'}

    중요 이슈: {', '.join(critical_issues) if critical_issues else '없음'}
    경고사항: {', '.join(warnings) if warnings else '없음'}
    권장사항: {', '.join(recommendations) if recommendations else '없음'}

    위 내용을 바탕으로 다음 사항을 포함하여 3~4문장으로 결론을 요약해 주세요:
    1. 전반적인 장비 상태
    2. 가장 심각한 센서들의 상태와 그 위험성
    3. 권장되는 조치사항
    """
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    
    conclusion = response["choices"][0]["message"]["content"]
    return conclusion

@router.get("/device_report_pdf/{device_id}")
async def generate_pdf_report(device_id: str):
    """PDF 리포트 생성"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()

        # 상태 정보 조회
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

        if not status_result or not analysis_result:
            raise HTTPException(status_code=404, detail="Device data not found")

        # 센서 상태 분류
        sensor_details = json.loads(analysis_result[6])
        critical_sensors = []
        warning_sensors = []
        caution_sensors = []
        
        for sensor_name, details in sensor_details.items():
            if details['status'] == '위험':
                critical_sensors.append((sensor_name, details['current_value']))
            elif details['status'] == '경고':
                warning_sensors.append((sensor_name, details['current_value']))
            elif details['status'] == '주의':
                caution_sensors.append((sensor_name, details['current_value']))

        # ChatGPT를 사용하여 결론 생성
        conclusion = generate_conclusion(device_id, analysis_result)

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ 
                    font-family: 'Malgun Gothic', sans-serif; 
                    margin: 40px; 
                }}
                .title {{
                    text-align: center;
                    font-weight: bold;
                    font-size: 20px;
                    margin-bottom: 20px;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: 20px;
                }}
                th, td {{
                    border: 1px solid black;
                    padding: 8px;
                    text-align: left;
                }}
                .conclusion {{
                    margin-top: 30px;
                    padding: 15px;
                    background-color: #f8f9fa;
                    border-left: 4px solid #4e73df;
                }}
                .conclusion-title {{
                    font-weight: bold;
                    margin-bottom: 10px;
                    color: #4e73df;
                }}
            </style>
        </head>
        <body>
            <div class="title">설비 이력 카드</div>
            
            <table>
                <tr>
                    <th>관리번호</th>
                    <td>{device_id}</td>
                    <th>설비명</th>
                    <td>{'AGV' if 'AGV' in device_id else 'OHT'}</td>
                </tr>
                <tr>
                    <th>현재상태</th>
                    <td colspan="3">{status_result[0]}</td>
                </tr>
                <tr>
                    <th>점검일시</th>
                    <td colspan="3">{status_result[1]}</td>
                </tr>
            </table>

            <table>
                <tr>
                    <th colspan="4">상태 분석</th>
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
                <tr>
                    <th colspan="2">분석 결과</th>
                </tr>
                <tr>
                    <th>요약</th>
                    <td>{analysis_result[2]}</td>
                </tr>
                <tr>
                    <th>중요 이슈</th>
                    <td>{', '.join(json.loads(analysis_result[3]))}</td>
                </tr>
                <tr>
                    <th>경고사항</th>
                    <td>{', '.join(json.loads(analysis_result[4]))}</td>
                </tr>
                <tr>
                    <th>권장사항</th>
                    <td>{', '.join(json.loads(analysis_result[5]))}</td>
                </tr>
                <tr>
                    <th>센서 상태</th>
                    <td>
                        <div>
                            ■ 위험 수준 센서: {', '.join([f"{name}: {value:.2f}" for name, value in critical_sensors]) if critical_sensors else '없음'}
                        </div>
                        <div>
                            ■ 경고 수준 센서: {', '.join([f"{name}: {value:.2f}" for name, value in warning_sensors]) if warning_sensors else '없음'}
                        </div>
                        <div>
                            ■ 주의 수준 센서: {', '.join([f"{name}: {value:.2f}" for name, value in caution_sensors]) if caution_sensors else '없음'}
                        </div>
                    </td>
                </tr>
            </table>

            <div class="conclusion">
                <div class="conclusion-title">AI 분석 결론</div>
                <div>{conclusion}</div>
            </div>
        </body>
        </html>
        """
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            HTML(string=html_content).write_pdf(tmp.name)
            return FileResponse(
                tmp.name,
                media_type='application/pdf',
                filename=f'{device_id}_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
        
# 전역 변수로 monitor 인스턴스 생성
device_monitor = DeviceMonitor()

# 모델 설정 추가
model_config = {
    "img_dim_h": 120,
    "img_dim_w": 160,
    "patch_size": 16,
    "embed_dim": 256,
    "num_heads": 8,
    "depth": 6,
    "aux_input_dim": 11,
    "num_classes": 4
}

@router.get("/device_status/{device_id}")
async def get_device_status(device_id: str):
    status = db.get_device_status(device_id)
    if not status:
        raise HTTPException(status_code=404, detail="Device not found")
    
    window_data = db.load_device_data(
        'OHT' if 'oht' in device_id.lower() else 'AGV', 
        device_id[-2:]
    )
    
    analyzer = ImprovedSensorAnalyzer(model_config)
    latest_analysis = analyzer.analyze_device_status(device_id, window_data.tail(300))
    
    status.update({
        "sensor_analysis": latest_analysis,
        "monitoring_in_progress": device_monitor.is_monitoring(device_id)
    })
    
    return status