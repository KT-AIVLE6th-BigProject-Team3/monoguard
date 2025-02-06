import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os
from glob import glob
import json
import zipfile
import zipfile
# 우선 agv/01/agv01_0901_0812에 있는 원천 데이터와 라벨링 데이터만 전처리

# 원천 데이터
root_raw_path = '3.개방데이터\\1.데이터\\1.Training\\1.원천데이터\\agv'
root_label_path = '3.개방데이터\\1.데이터\\1.Training\\2.라벨링데이터\\agv'
numbers_path_list = os.listdir(root_raw_path) # 01 폴더, 02 폴더, ... 16폴더
recursive_path_list = os.listdir(os.path.join(root_raw_path,numbers_path_list[0])) # agv01_0901_0812, agv01_0902_1253,...,agv01_1027_1405
# return된 중요한 변수는 bin_files,features_files, label_json_files 과 같은 원천데이터와 라벨링 데이터

def sort_and_list(root_raw_path:str,root_label_path:str,number:str,recursive_path:str) -> tuple:
    """멀티 모달의 데이터의 파일 경로들을 전처리하는 함수입니다.
       (bin_files:List, features_files:List,label_json_files:List)와 같이 반환됩니다.
       각각의 bin_file은 bin파일이 담긴 리스트, features_files는 원천 데이터의 온도,전류,미세먼지 센서데이터가 있는 파일 리스트, label_json_files는 라벨링 데이터가 담긴 json파일들이 존재합니다.
    """
    target_path = os.path.join(root_raw_path,number,recursive_path)
    bin_files = glob(target_path + '\*.bin') # 원천 데이터의 bin파일
    features_files = glob(target_path + '\*.csv') # 원천 데이터의 csv파일
    
    target_label_path = os.path.join(root_label_path,number,recursive_path)
    label_json_files = glob(target_label_path+'\*.json')
    return bin_files,features_files,label_json_files

def transition_json_to_dataframe(label_json_files:list):
    """json파일의 라벨링 데이터가 담긴 리스트로 부터 각각의 json파일로부터 필요한 외부 데이터(외부온도, 외부습도, 조도)와 정답 데이터(state) 파싱"""
    dataframe = pd.DataFrame()
    for i in label_json_files:
        with open(i,'r',encoding='utf-8') as file:
            data = json.load(file)
            state = data['annotations'][0]['tagging'][0]['state'] # 기기 상태 0이면 정상 1이면 비정상
            ex_temperature = data['external_data'][0]['ex_temperature'][0]['value']
            ex_humidity = data['external_data'][0]['ex_humidity'][0]['value']
            ex_illuminance = data['external_data'][0]['ex_illuminance'][0]['value']
            device_name = data['meta_info'][0]['device_name']
            collection_date = data['meta_info'][0]['collection_date']
            collection_time = data['meta_info'][0]['collection_time']
            cumulative_operating_day = data['meta_info'][0]['cumulative_operating_day']
            temp = pd.DataFrame({'device_name':[device_name],'collection_date': [collection_date], 'collection_time':[collection_time], 
                                 'cumulative_operating_day':[cumulative_operating_day],'ex_temperature':[ex_temperature],'ex_humidity':[ex_humidity],
                                 'ex_illuminance':[ex_illuminance],'state':[state]})
            dataframe = pd.concat([dataframe,temp],ignore_index=True)
    return dataframe

def transition_feature_to_dataframe(features_files:list):
    """NTC, PM.1.0 과 같이 피쳐가 담긴 csv파일 List를 DataFrame으로 정리하는 함수"""
    dataframe = pd.DataFrame()
    for i in features_files:
        temp = pd.read_csv(i)
        dataframe = pd.concat([dataframe,temp],ignore_index=True)
    dataframe = pd.concat([pd.DataFrame({'filenames':features_files}),dataframe],axis=1)
    dataframe['filenames']=dataframe['filenames'].apply(lambda x: x.rsplit('.', 1)[0] + '.bin')
    return dataframe

def make_final_dataframe(label_dataframe,feature_dataframe):
    return pd.concat([feature_dataframe,label_dataframe],axis=1)

def extract_zipfile(zipfilepath,destination_path):
    """압축해체"""
    with zipfile.ZipFile(zipfilepath,'r') as zip_ref:
        zip_ref.extractall(destination_path)
    print(f'{destination_path} 디렉토리에 성공적으로 해제')

