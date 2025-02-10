import numpy as np
import pandas as pd
from typing import Dict
from scipy.stats import norm

class ImprovedSensorAnalyzer:
    def __init__(self, model_config):
        self.model_config = model_config
        self.device = 'cpu'
        self.sensor_columns = ['NTC', 'PM1_0', 'PM2_5', 'PM10', 'CT1', 'CT2', 'CT3', 'CT4',
                             'ex_temperature', 'ex_humidity', 'ex_illuminance']
        
        # AGV 센서 임계값
        self.agv_sensor_distributions = {
            'NTC': {
                '정상': {'mu': 25.066730, 'sigma': 2.1},
                '주의': {'mu': 33.656681, 'sigma': 3.2}, 
                '경고': {'mu': 46.044304, 'sigma': 4.5},
                '위험': {'mu': 55.998341, 'sigma': 5.1}
            },
            'PM10': {
                '정상': {'mu': 46.285282, 'sigma': 5.2},
                '주의': {'mu': 65.315544, 'sigma': 6.8},
                '경고': {'mu': 79.276268, 'sigma': 7.9}, 
                '위험': {'mu': 83.203209, 'sigma': 8.4}
            },
            'PM2_5': {
                '정상': {'mu': 26.641882, 'sigma': 2.5},
                '주의': {'mu': 36.201855, 'sigma': 3.5},
                '경고': {'mu': 44.089832, 'sigma': 4.2},
                '위험': {'mu': 46.203209, 'sigma': 4.8}
            },
            'PM1_0': {
                '정상': {'mu': 21.076632, 'sigma': 2.3},
                '주의': {'mu': 30.907192, 'sigma': 3.1},
                '경고': {'mu': 37.252541, 'sigma': 3.8},
                '위험': {'mu': 38.946526, 'sigma': 4.2}
            },
            'CT1': {
                '정상': {'mu': 1.873255, 'sigma': 0.2},
                '주의': {'mu': 1.917726, 'sigma': 0.4},
                '경고': {'mu': 1.914407, 'sigma': 0.8},
                '위험': {'mu': 1.914225, 'sigma': 1.2}
            },
            'CT2': {
                '정상': {'mu': 74.913399, 'sigma': 2.5},
                '주의': {'mu': 77.878395, 'sigma': 3.5},
                '경고': {'mu': 106.112183, 'sigma': 5.2},
                '위험': {'mu': 204.224701, 'sigma': 8.4}
            },
            'CT3': {
                '정상': {'mu': 49.737854, 'sigma': 2.1},
                '주의': {'mu': 50.575222, 'sigma': 3.2},
                '경고': {'mu': 61.315948, 'sigma': 4.5},
                '위험': {'mu': 85.934441, 'sigma': 6.8}
            },
            'CT4': {
                '정상': {'mu': 19.710432, 'sigma': 1.8},
                '주의': {'mu': 21.076891, 'sigma': 2.5},
                '경고': {'mu': 29.155102, 'sigma': 3.6},
                '위험': {'mu': 64.330429, 'sigma': 5.2}
            },
            'ex_temperature': {
                '정상': {'mu': 25.484825, 'sigma': 0.5},
                '주의': {'mu': 25.464037, 'sigma': 0.8},
                '경고': {'mu': 25.491526, 'sigma': 1.2},
                '위험': {'mu': 25.486631, 'sigma': 1.5}
            },
            'ex_humidity': {
                '정상': {'mu': 30.484825, 'sigma': 1.2},
                '주의': {'mu': 30.596287, 'sigma': 1.8},
                '경고': {'mu': 30.481356, 'sigma': 2.4},
                '위험': {'mu': 30.582888, 'sigma': 3.0}
            },
            'ex_illuminance': {
                '정상': {'mu': 155.632019, 'sigma': 2.5},
                '주의': {'mu': 155.566132, 'sigma': 3.5},
                '경고': {'mu': 155.376266, 'sigma': 4.8},
                '위험': {'mu': 155.069519, 'sigma': 6.2}
            }
        }
        
        # OHT 센서 임계값 (더 높은 임계값 설정)
        self.oht_sensor_distributions = {
            'NTC': {
                '정상': {'mu': 27.457478, 'sigma': 0.85},
                '주의': {'mu': 29.167545, 'sigma': 4.02}, 
                '경고': {'mu': 37.200157, 'sigma': 5.80},
                '위험': {'mu': 48.797676, 'sigma': 6.25}
            },
            'PM10': {
                '정상': {'mu': 20.000673, 'sigma': 0.007},
                '주의': {'mu': 19.989773, 'sigma': 0.007},
                '경고': {'mu': 20.004225, 'sigma': 0.009}, 
                '위험': {'mu': 19.985994, 'sigma': 0.010}
            },
            'PM2_5': {
                '정상': {'mu': 11.746469, 'sigma': 0.130},
                '주의': {'mu': 12.007955, 'sigma': 0.011},
                '경고': {'mu': 12.029567, 'sigma': 0.015},
                '위험': {'mu': 12.000000, 'sigma': 0.015}
            },
            'PM1_0': {
                '정상': {'mu': 8.000672, 'sigma': 0.003},
                '주의': {'mu': 8.006818, 'sigma': 0.015},
                '경고': {'mu': 7.976769, 'sigma': 0.002},
                '위험': {'mu': 7.971989, 'sigma': 0.002}
            },
            'CT1': {
                '정상': {'mu': 2.339913, 'sigma': 0.318},
                '주의': {'mu': 2.976932, 'sigma': 1.535},
                '경고': {'mu': 6.048205, 'sigma': 3.296},
                '위험': {'mu': 12.640952, 'sigma': 4.150}
            },
            'CT2': {
                '정상': {'mu': 1.114257, 'sigma': 0.990},
                '주의': {'mu': 3.095295, 'sigma': 10.662},
                '경고': {'mu': 24.420654, 'sigma': 37.034},
                '위험': {'mu': 98.488770, 'sigma': 42.500}
            },
            'CT3': {
                '정상': {'mu': 0.500235, 'sigma': 0.389},
                '주의': {'mu': 1.278580, 'sigma': 4.290},
                '경고': {'mu': 9.859504, 'sigma': 13.822},
                '위험': {'mu': 37.503109, 'sigma': 15.600}
            },
            'CT4': {
                '정상': {'mu': 0.479254, 'sigma': 0.208},
                '주의': {'mu': 0.896784, 'sigma': 1.793},
                '경고': {'mu': 4.483538, 'sigma': 6.701},
                '위험': {'mu': 17.886246, 'sigma': 7.850}
            },
            'ex_temperature': {
                '정상': {'mu': 22.497646, 'sigma': 0.003},
                '주의': {'mu': 22.492046, 'sigma': 0.018},
                '경고': {'mu': 22.456177, 'sigma': 0.032},
                '위험': {'mu': 22.521008, 'sigma': 0.035}
            },
            'ex_humidity': {
                '정상': {'mu': 35.482178, 'sigma': 0.0002},
                '주의': {'mu': 35.481819, 'sigma': 0.010},
                '경고': {'mu': 35.501583, 'sigma': 0.015},
                '위험': {'mu': 35.498600, 'sigma': 0.020}
            },
            'ex_illuminance': {
                '정상': {'mu': 520.163391, 'sigma': 0.050},
                '주의': {'mu': 520.262512, 'sigma': 0.088},
                '경고': {'mu': 520.438232, 'sigma': 0.204},
                '위험': {'mu': 520.030823, 'sigma': 0.250}
            }
        }

        self.agv_status_messages = {
            '정상': {
                'NTC': "AGV 동작 온도 22-26℃ 유지 중. 냉각 시스템 정상 작동",
                'PM': "AGV 작업 구역 미세먼지 농도 정상 (PM10 < 50µg/m³, PM2.5 < 25µg/m³)",
                'CT': "AGV 모터 소비전류 정격 범위 내 동작 중 (정격전류의 60-80%)",
                'ex_temperature': "작업장 온도 18-28℃ 유지 중. 최적 작업 환경 조성",
                'ex_humidity': "작업장 습도 40-60% 유지 중. 쾌적도 양호",
                'ex_illuminance': "작업장 조도 750-1500lux 유지 중. 시야 확보 양호"
            },
            '주의': {
                'NTC': "AGV 동작 온도 27-32℃ 감지. 냉각팬 RPM 및 방열판 상태 점검 필요",
                'PM': "미세먼지 농도 상승 (PM10 > 80µg/m³, PM2.5 > 35µg/m³). 공조 시스템 점검",
                'CT': "모터 소비전류 정격의 85% 수준. 부하 분산 및 구동부 마찰 검사 필요",
                'ex_temperature': "작업장 온도 범위 이탈 (15-17℃ 또는 29-32℃). 공조 시스템 점검 필요",
                'ex_humidity': "작업장 습도 범위 이탈 (30-39% 또는 61-70%). 습도 조절 필요",
                'ex_illuminance': "작업장 조도 저하 (500-750lux). 조명 시설 점검 필요"
            },
            '경고': {
                'NTC': "AGV 동작 온도 33-38℃ 감지. 24시간 내 냉각 시스템 전체 점검 필요",
                'PM': "고농도 미세먼지 감지 (PM10 > 120µg/m³, PM2.5 > 75µg/m³). 필터 교체 필요",
                'CT': "모터 소비전류 정격의 95% 초과. 6시간 내 과부하 원인 분석 필요",
                'ex_temperature': "작업장 온도 주의 (10-14℃ 또는 33-35℃). 작업자 보호 장비 착용 필요",
                'ex_humidity': "작업장 습도 주의 (20-29% 또는 71-80%). 응축/정전기 위험 확인",
                'ex_illuminance': "작업장 조도 주의 (300-500lux). 보조 조명 설치 필요"
            },
            '위험': {
                'NTC': "AGV 온도 39℃ 이상 감지. 즉시 운행 중지 필요. ▶관리팀 긴급 코드: T-RED, 설비팀 핫라인(#9111) 즉시 연락 필요",
                'PM': "위험 수준 미세먼지 감지 (PM10 > 150µg/m³, PM2.5 > 100µg/m³). 작업 중단 필요. ▶관리팀 긴급 코드: P-RED, 환경안전팀(#9112) 즉시 보고",
                'CT': "모터 정격전류 초과 감지. 즉시 전원 차단 필요. ▶관리팀 긴급 코드: C-RED, 전기안전팀(#9113) 긴급 출동 요청",
                'ex_temperature': "작업장 온도 위험 수준 (<10℃ 또는 >35℃). 작업 중단 필요. ▶관리팀 긴급 코드: E-RED, 설비관리팀(#9114) 긴급 점검 요청",
                'ex_humidity': "작업장 습도 위험 수준 (<20% 또는 >80%). 장비 보호 필요. ▶관리팀 긴급 코드: H-RED, 설비관리팀(#9114) 긴급 조치 요청",
                'ex_illuminance': "작업장 조도 위험 수준 (<300lux). 안전사고 위험. ▶관리팀 긴급 코드: L-RED, 전기안전팀(#9113) 긴급 조치 요청"
            }

        }
        
        self.oht_status_messages = {
            '정상': {
                'NTC': "OHT 시스템 온도 20-25℃ 유지 중. 정상 범위 내 동작",
                'PM': "OHT 레일 구역 청정도 양호 (PM10 < 30µg/m³, PM2.5 < 15µg/m³)",
                'CT': "호이스트 모터 정격전류 범위 내 안정적 동작 중 (정격의 50-70%)",
                'ex_temperature': "OHT 작업구역 온도 18-28℃ 유지 중. 최적 운영 조건",
                'ex_humidity': "OHT 작업구역 습도 40-60% 유지 중. 결로 없음",
                'ex_illuminance': "OHT 작업구역 조도 1000-2000lux 유지 중. 작업 시야 양호"
            },
            '주의': {
                'NTC': "OHT 시스템 온도 26-30℃ 감지. 냉각 시스템 성능 점검 권장",
                'PM': "레일 구역 미세먼지 농도 증가 (PM10 > 50µg/m³, PM2.5 > 25µg/m³). 환기 필요",
                'CT': "호이스트 전류 증가 (정격의 75-85%). 부하 체크 및 케이블 점검 필요",
                'ex_temperature': "OHT 구역 온도 범위 이탈 (15-17℃ 또는 29-32℃). 온도 관리 필요",
                'ex_humidity': "OHT 구역 습도 범위 이탈 (30-39% 또는 61-70%). 습도 조절 필요",
                'ex_illuminance': "OHT 구역 조도 저하 (800-1000lux). 조명 시설 점검 필요"
            },
            '경고': {
                'NTC': "OHT 시스템 온도 31-35℃ 감지. 12시간 내 방열 시스템 점검 필요",
                'PM': "레일 미세먼지 주의 수준 (PM10 > 80µg/m³, PM2.5 > 50µg/m³). 클리닝 필요",
                'CT': "호이스트 과전류 위험 (정격의 90%). 4시간 내 구동 시스템 점검 필요",
                'ex_temperature': "OHT 구역 온도 주의 (10-14℃ 또는 33-35℃). 운행 속도 조정 필요",
                'ex_humidity': "OHT 구역 습도 주의 (20-29% 또는 71-80%). 결로 위험 확인",
                'ex_illuminance': "OHT 구역 조도 주의 (500-800lux). 운행 속도 저감 필요"
            },
            '위험': {
                'NTC': "OHT 시스템 온도 36℃ 이상. 즉시 운행 중지 필요. ▶관리팀 긴급 코드: HT-RED, OHT정비팀(#9211) 긴급 출동 요청",
                'PM': "레일 구역 미세먼지 위험 수준 (PM10 > 100µg/m³, PM2.5 > 75µg/m³). 운행 중단 필요. ▶관리팀 긴급 코드: HP-RED, 환경관리팀(#9212) 즉시 보고",
                'CT': "호이스트 정격전류 초과. 즉시 비상정지 필요. ▶관리팀 긴급 코드: HC-RED, 호이스트정비팀(#9213) 긴급 출동 요청",
                'ex_temperature': "OHT 구역 온도 위험 수준 (<10℃ 또는 >35℃). 운행 중단 필요. ▶관리팀 긴급 코드: HE-RED, 시설관리팀(#9214) 긴급 점검 요청",
                'ex_humidity': "OHT 구역 습도 위험 수준 (<20% 또는 >80%). 설비 보호 필요. ▶관리팀 긴급 코드: HH-RED, 시설관리팀(#9214) 긴급 조치 요청",
                'ex_illuminance': "OHT 구역 조도 위험 수준 (<500lux). 즉시 운행 중단. ▶관리팀 긴급 코드: HL-RED, 전기설비팀(#9215) 긴급 조치 요청"
            }
        }

    def calculate_state_probabilities(self, sensor: str, value: float, device_id: str) -> Dict[str, float]:
        # 장비 타입에 따라 적절한 분포 선택
        is_oht = 'oht' in device_id.lower()
        distributions = self.oht_sensor_distributions if is_oht else self.agv_sensor_distributions
        
        if sensor not in distributions:
            return {'정상': 0.25, '주의': 0.25, '경고': 0.25, '위험': 0.25}
            
        sensor_dist = distributions[sensor]
        likelihoods = {
            state: norm.pdf(value, dist['mu'], dist['sigma'])
            for state, dist in sensor_dist.items()
        }
        
        total = sum(likelihoods.values())
        if total == 0:
            return {'정상': 0.25, '주의': 0.25, '경고': 0.25, '위험': 0.25}
            
        return {state: likelihood/total for state, likelihood in likelihoods.items()}

    def analyze_device_status(self, device_id: str, window_data: pd.DataFrame) -> Dict:
        try:
            sensor_details = {}
            critical_messages = []
            warning_messages = []
            latest_data = window_data.iloc[-1]

            for sensor in self.sensor_columns:
                current_value = float(latest_data[sensor])
                probabilities = self.calculate_state_probabilities(sensor, current_value, device_id)
                
                status = max(probabilities.items(), key=lambda x: x[1])[0]
                message = self._get_sensor_message(sensor, current_value, status, device_id)
                
                if message:
                    if status == '위험':
                        critical_messages.append(message)
                    elif status == '경고':
                        warning_messages.append(message)

                values = window_data[sensor].values
                mean_value = np.mean(values)
                std_value = np.std(values)
                
                is_oht = 'oht' in device_id.lower()
                distributions = self.oht_sensor_distributions if is_oht else self.agv_sensor_distributions
                normal_range = self._get_normal_range(sensor, distributions)
                
                sensor_details[sensor] = {
                    'current_value': current_value,
                    'mean': mean_value,
                    'std': std_value,
                    'normal_range': normal_range,
                    'status': status,
                    'message': message,
                    'state_probabilities': probabilities
                }

            summary = self._generate_summary(critical_messages, warning_messages)
            recommendations = self._generate_recommendations(critical_messages, warning_messages)

            return {
                'device_id': device_id,
                'summary': summary,
                'sensor_details': sensor_details,
                'critical_issues': critical_messages,
                'warnings': warning_messages,
                'recommendations': recommendations
            }

        except Exception as e:
            print(f"Analysis failed for {device_id}: {str(e)}")
            raise

    def _get_sensor_message(self, sensor: str, value: float, status: str, device_id: str) -> str:
        if status == '정상':
            return ''
            
        is_oht = 'oht' in device_id.lower()
        messages = self.oht_status_messages if is_oht else self.agv_status_messages
        
        sensor_type = 'NTC' if sensor == 'NTC' else 'PM' if sensor.startswith('PM') else 'CT'
        return messages[status][sensor_type]
    def _get_normal_range(self, sensor: str, distributions: dict) -> Dict[str, float]:
        if sensor in distributions:
            dist = distributions[sensor]['정상']
            return {
                'min': dist['mu'] - 2 * dist['sigma'],
                'max': dist['mu'] + 2 * dist['sigma']
            }
        return {'min': 0, 'max': 100}
    def _generate_summary(self, critical_messages: list, warning_messages: list) -> str:
        if critical_messages:
            return "즉각적인 점검이 필요한 센서가 있습니다."
        elif warning_messages:
            return "주의가 필요한 센서가 있습니다."
        return "모든 센서가 정상 범위 내에서 동작 중입니다."

    def _generate_recommendations(self, critical_messages: list, warning_messages: list) -> list:
        recommendations = []
        
        if critical_messages:
            recommendations.append("위험 상태인 센서의 즉각적인 점검이 필요합니다.")
            if any("온도" in msg for msg in critical_messages):
                recommendations.append("온도가 높은 구역의 냉각 시스템을 점검하세요.")
            if any("전류" in msg for msg in critical_messages):
                recommendations.append("전류 이상이 감지된 모터의 상태를 점검하세요.")
        
        if warning_messages:
            recommendations.append("주의 상태인 센서들의 상태를 지속적으로 모니터링하세요.")
            if any("먼지" in msg for msg in warning_messages):
                recommendations.append("먼지 농도가 높은 구역의 환기 시스템을 점검하세요.")
            if any("온도" in msg for msg in warning_messages):
                recommendations.append("온도 상승 추세를 모니터링하고 필요시 냉각 시스템을 가동하세요.")
        
        if not critical_messages and not warning_messages:
            recommendations.extend([
                "정기적인 유지보수를 계속 진행하세요.",
                "센서 데이터를 주기적으로 백업하고 분석하세요."
            ])
            
        return recommendations