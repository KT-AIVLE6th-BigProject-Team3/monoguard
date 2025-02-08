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
                '정상': {'mu': 25.415476, 'sigma': 2.1},
                '주의': {'mu': 34.446518, 'sigma': 3.2}, 
                '경고': {'mu': 46.821117, 'sigma': 4.5},
                '위험': {'mu': 56.268467, 'sigma': 5.1}
            },
            'PM10': {
                '정상': {'mu': 46.191109, 'sigma': 5.2},
                '주의': {'mu': 65.476875, 'sigma': 6.8},
                '경고': {'mu': 79.573204, 'sigma': 7.9}, 
                '위험': {'mu': 83.664932, 'sigma': 8.4}
            },
            'PM2_5': {
                '정상': {'mu': 26.609423, 'sigma': 2.5},
                '주의': {'mu': 36.223568, 'sigma': 3.5},
                '경고': {'mu': 43.976044, 'sigma': 4.2},
                '위험': {'mu': 46.158443, 'sigma': 4.8}
            },
            'PM1_0': {
                '정상': {'mu': 20.998859, 'sigma': 2.3},
                '주의': {'mu': 30.432819, 'sigma': 3.1},
                '경고': {'mu': 36.614906, 'sigma': 3.8},
                '위험': {'mu': 38.270130, 'sigma': 4.2}
            },
            'CT1': {
                '정상': {'mu': 1.892173, 'sigma': 0.2},
                '주의': {'mu': 2.270132, 'sigma': 0.4},
                '경고': {'mu': 5.033443, 'sigma': 0.8},
                '위험': {'mu': 10.855429, 'sigma': 1.2}
            },
            'CT2': {
                '정상': {'mu': 74.927582, 'sigma': 2.5},
                '주의': {'mu': 77.913864, 'sigma': 3.5},
                '경고': {'mu': 104.485428, 'sigma': 5.2},
                '위험': {'mu': 195.490448, 'sigma': 8.4}
            },
            'CT3': {
                '정상': {'mu': 49.747871, 'sigma': 2.1},
                '주의': {'mu': 51.029758, 'sigma': 3.2},
                '경고': {'mu': 61.031021, 'sigma': 4.5},
                '위험': {'mu': 92.384338, 'sigma': 6.8}
            },
            'CT4': {
                '정상': {'mu': 19.719061, 'sigma': 1.8},
                '주의': {'mu': 21.084173, 'sigma': 2.5},
                '경고': {'mu': 30.545572, 'sigma': 3.6},
                '위험': {'mu': 63.257923, 'sigma': 5.2}
            },
            'ex_temperature': {
                '정상': {'mu': 25.494680, 'sigma': 0.5},
                '주의': {'mu': 25.464758, 'sigma': 0.8},
                '경고': {'mu': 25.480036, 'sigma': 1.2},
                '위험': {'mu': 25.480520, 'sigma': 1.5}
            },
            'ex_humidity': {
                '정상': {'mu': 30.464285, 'sigma': 1.2},
                '주의': {'mu': 30.569384, 'sigma': 1.8},
                '경고': {'mu': 30.417036, 'sigma': 2.4},
                '위험': {'mu': 30.498701, 'sigma': 3.0}
            },
            'ex_illuminance': {
                '정상': {'mu': 155.609421, 'sigma': 2.5},
                '주의': {'mu': 155.480179, 'sigma': 3.5},
                '경고': {'mu': 155.352264, 'sigma': 4.8},
                '위험': {'mu': 155.241562, 'sigma': 6.2}
            }
        }

        self.agv_status_messages = {
            '정상': {
                'NTC': "AGV 모터 온도가 정상 범위 내에서 안정적입니다.",
                'PM': "AGV 주행 환경의 먼지 농도가 정상 수준입니다.",
                'CT': "AGV 구동 모터의 전류값이 정상 범위입니다."
            },
            '주의': {
                'NTC': "AGV 모터 온도가 상승 중입니다. 주행 속도 조정이 필요합니다.",
                'PM': "AGV 주행로의 먼지 농도가 높아졌습니다. 청소가 필요합니다.",
                'CT': "AGV 구동 모터의 전류 소비가 증가했습니다. 부하 확인이 필요합니다."
            },
            '경고': {
                'NTC': "AGV 모터 과열 위험이 있습니다. 즉시 감속이 필요합니다.",
                'PM': "AGV 주행로의 먼지가 심각합니다. 즉시 청소가 필요합니다.",
                'CT': "AGV 구동 모터에 과부하가 발생했습니다. 화물 중량 확인이 필요합니다."
            },
            '위험': {
                'NTC': "AGV 모터가 심각한 과열 상태입니다. 즉시 정지하세요.",
                'PM': "AGV 주행로가 심각하게 오염되었습니다. 운행을 중지하세요.",
                'CT': "AGV 구동 모터가 위험합니다. 즉시 전원을 차단하세요."
            }
        }
        
        self.oht_status_messages = {
            '정상': {
                'NTC': "OHT 구동부 온도가 정상 범위입니다.",
                'PM': "OHT 레일 환경의 먼지 농도가 정상입니다.",
                'CT': "OHT 호이스트 모터의 전류값이 정상입니다."
            },
            '주의': {
                'NTC': "OHT 구동부 온도가 상승 중입니다. 호이스팅 속도를 조정하세요.",
                'PM': "OHT 레일의 먼지 농도가 높아졌습니다. 레일 청소가 필요합니다.",
                'CT': "OHT 호이스트 전류가 증가했습니다. 와이어로프 상태를 확인하세요."
            },
            '경고': {
                'NTC': "OHT 구동부 과열 위험이 있습니다. 부하를 줄이세요.",
                'PM': "OHT 레일이 심각하게 오염되었습니다. 즉시 청소가 필요합니다.",
                'CT': "OHT 호이스트에 과부하가 발생했습니다. 즉시 하중을 확인하세요."
            },
            '위험': {
                'NTC': "OHT 구동부가 심각한 과열 상태입니다. 운행을 중지하세요.",
                'PM': "OHT 레일 상태가 위험합니다. 즉시 정비가 필요합니다.",
                'CT': "OHT 호이스트가 위험합니다. 즉시 비상정지하세요."
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