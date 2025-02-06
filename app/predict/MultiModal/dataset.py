import torch
import pandas
import numpy as np
from torch.utils.data import Dataset
import os
import pandas as pd
class MultimodalDataset(Dataset):
    """사용자 정의 멀티모달 데이터셋"""
    def __init__(self, X: pandas.DataFrame, y: pandas.Series):
        """필요한 데이터를 이곳에서 선언
        Parameter:
        X: 열화상 이미지와 센서데이터의 데이터 프레임
        y: 정답 데이터
        """
        self.X = X
        self.y = y

    def __getitem__(self, index):
        """열화상 이미지 [1,120,160] 크기와 센서 데이터 11개의 칼럼 그리고 이에 해당하는 정답 데이터 반환"""
        image = torch.tensor(np.load(self.X.iloc[index]['filenames']), dtype=torch.float32).unsqueeze(0)
        sensor_features = self.X.drop(columns=['filenames'])
        sensor_features = torch.tensor(sensor_features.iloc[index].values, dtype=torch.float32)
        label = int(self.y.iloc[index])  # 정답 데이터 반환
        return image, sensor_features, label

    def __len__(self):
        return len(self.X)


class MultimodalTestDataset(Dataset):
    """사용자 정의 멀티모달 데이터셋"""
    def __init__(self, X: pandas.DataFrame):
        """필요한 데이터를 이곳에서 선언
            Parameter:
            X: 열화상 이미지와 센서데이터의 데이터 프레임
            """
        self.X = X

    def __getitem__(self, index):
        """열화상 이미지 [1,120,160] 크기와 센서 데이터 11개의 칼럼 반환"""
        image = torch.tensor(np.load(self.X.iloc[index]['filenames']), dtype=torch.float32).unsqueeze(0)
        sensor_features = self.X.drop(columns=['filenames'])
        sensor_features = torch.tensor(sensor_features.iloc[index].values, dtype=torch.float32)
        return image, sensor_features

    def __len__(self):
        return len(self.X)
    
class MultimodalDataset2(torch.utils.data.Dataset):
    def __init__(self, csv_path, bin_root_folder, split_folder, img_dim_h, img_dim_w):
        self.data = []
        self.img_dim_h = img_dim_h
        self.img_dim_w = img_dim_w

        # 모든 BIN 파일의 경로 수집
        bin_files = {}
        split_path = os.path.join(bin_root_folder, split_folder)
        for root, _, files in os.walk(split_path):
            for file in files:
                if file.endswith(".bin"):
                    bin_files[file] = os.path.join(root, file)

        # CSV 파일 읽기
        df = pd.read_csv(csv_path)
        features = ["NTC", "PM10", "PM2.5", "PM1.0",
                    "CT1", "CT2", "CT3", "CT4",
                    "temp_max_value", "ex_temperature", "ex_humidity", "ex_illuminance"]

        for _, row in df.iterrows():
            bin_filename = row['bin_filename']
            if bin_filename in bin_files:
                bin_path = bin_files[bin_filename]
                try:
                    img_data = np.load(bin_path).reshape((img_dim_h, img_dim_w))
                except Exception as e:
                    print(f"[Error] BIN 파일 로드 실패: {bin_path}, {e}")
                    continue

                aux_data = row[features].values.astype(np.float32)
                label = int(row['state'])
                self.data.append((img_data, aux_data, label))

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        img_data, aux_data, label = self.data[idx]
        img_data = torch.tensor(img_data, dtype=torch.float32).unsqueeze(0)
        aux_data = torch.tensor(aux_data, dtype=torch.float32)
        label = torch.tensor(label, dtype=torch.long)
        return img_data, aux_data, label