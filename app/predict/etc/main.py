from MultiModal.dataset import MultimodalDataset
from MultiModal.model import CrossAttention, SoftLabelEncoder, ViTFeatureExtractor, ConditionClassifier
from torch.utils.data import DataLoader
import joblib
import torch
import joblib
from Engine.utils import Evaluation_Classification_Model
import torch.nn.functional as F
# from warnings import filterwarnings
# filterwarnings(action='ignore')
from sklearn.model_selection import train_test_split

device = 'cuda' # GPU 설정 | GPU가 없으면 'cpu'로 바꿔주세요.

img_dim_h = 120  # 열화상 이미지 세로 크기
img_dim_w = 160  # 열화상 이미지 가로 크기
patch_size = 16
embed_dim = 128
num_heads = 4
depth = 6
aux_input_dim = 11  # 보조 데이터 차원 (예: 온도, 습도 등)
num_classes = 4  # 0:정상,1:관심,2:주의,3:위험

## 최적화 모델 불러오기
def load_AGV_model(Model_Parameter='Parameters/AGV_Best_State_Model.pth'):
    model = ConditionClassifier(img_dim_w, img_dim_h, patch_size, embed_dim, num_heads, depth, aux_input_dim, num_classes)
    model.load_state_dict(torch.load(Model_Parameter))
    return model.eval()

def load_OHT_model(Model_Parameter='Parameters/OHT_Best_State_Model.pth'):
    model = ConditionClassifier(img_dim_w, img_dim_h, patch_size, embed_dim, num_heads, depth, aux_input_dim, num_classes)
    model.load_state_dict(torch.load(Model_Parameter))
    return model.eval()

AGVConditionClassifier = load_AGV_model()
OHTConditionClassifier = load_OHT_model()

## 데이터 파이프라인 구축
seperate_col = ['device_id','collection_date','collection_time','cumulative_operating_day','state']
agv_dataset = joblib.load('DataFrame/agv_dataframe_version_2.pkl') # 데이터 프레임 불러오기
agv_X, agv_y = agv_dataset.drop(columns=seperate_col),agv_dataset['state'] # X,y 분리 (X는 이미지 + 센서 데이터, y는 state(정답값))
_, agv_X_test, _, agv_y_test = train_test_split(agv_X,agv_y,test_size=0.3,shuffle=False) # 모델은 이미 X_train은 학습했으므로 X_test만 필요


oht_dataset = joblib.load('DataFrame/oht_dataframe_version_2.pkl') # 데이터 프레임 불러오기
oht_X, oht_y = oht_dataset.drop(columns=seperate_col),oht_dataset['state'] # X,y 분리 (X는 이미지 + 센서 데이터, y는 state(정답값))
_,oht_X_test,_,oht_y_test = train_test_split(oht_X,oht_y,test_size=0.3,shuffle=False) # 모델은 이미 X_train은 학습했으므로 X_test만 필요

agv_test_dataset = MultimodalDataset(agv_X_test,agv_y_test) # 파이토치 멀티모달 데이터셋 선언
oht_test_dataset = MultimodalDataset(oht_X_test,oht_y_test) # 파이토치 멀티모달 데이터셋 선언

agv_test_dataloader = DataLoader(agv_test_dataset,batch_size=16,shuffle=False) # agv_test_dataloader (데이터 파이프라인) 선언 # 배치 사이즈는 마음대로 정할 수 있습니다.
oht_test_dataloader = DataLoader(oht_test_dataset,batch_size=16,shuffle=False) # oht_test_dataloader (데이터 파이프라인) 선언

## batch_size를 4로 입력하면 dataloader에서 image: [4,1,120,160]: 열화상 이미지 (흑백) 4장 | 센서데이터(칼럼 11개): [4,11] 4행 11열의 데이터 | target: [4,1]가 만들어집니다.
# agv_test_dataloader = iter(agv_test_dataloader)
# images, sensors, targets = next(agv_test_dataloader)
# print(images.shape, sensors.shape, targets)
# # 위 주석 코드를 돌리면 데이터 규격을 확인할 수 있고 중요한 것은 데이터 규격을 이미지: [N,1,120,160] | 센서데이터: [N,11]로 맞춰주기만 하면 모델이 입력돼서 예측값을 볼 수 있음.
# print(AGVConditionClassifier(images,sensors)) # Logits 값 출력
# print(F.softmax(AGVConditionClassifier(images,sensors),dim=1)) # 확률값 출력
# print(torch.argmax(F.softmax(AGVConditionClassifier(images,sensors),dim=1),dim=1)) # 정답값 출력 
# dim은 1로 무조건 설정

# AGV | OHT 평가
oht_y_true, oht_y_pred = Evaluation_Classification_Model(OHTConditionClassifier,oht_test_dataloader,'OHTClassification') 
agv_y_true, agv_y_pred = Evaluation_Classification_Model(AGVConditionClassifier,agv_test_dataloader,'AGVClassification')

## 만약 Input type (torch.cuda.FloatTensor) and weight type should be the same 에러가 난다면
## 데이터와 모델이 같은 GPU 선상에 있어야한다는 의미이다.
## model.to('cpu') 나 data.to('cpu') 를 이용해서 두 환경을 맞춰주어야 평가가 진행이 됩니다.
