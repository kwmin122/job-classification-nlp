"""
직무 분류 predict 코드
새 채용공고 텍스트를 입력하면 직무군을 분류합니다.
사용법: python predict.py
"""

import sys
sys.path = [p for p in sys.path if '김유민' not in p]

import pickle
import numpy as np
import re
from collections import Counter

import torch
import torch.nn as nn
from torch.nn.utils.rnn import pad_sequence
from torch.utils.data import Dataset, DataLoader

from gensim.models.fasttext import load_facebook_vectors
from sklearn.preprocessing import LabelEncoder
import joblib

# ─────────────────────────────────────────
# 설정
# ─────────────────────────────────────────

DATA_PATH     = 'preprocessed_data.pkl'
SVM_PATH      = 'model_tfidf_svm.pkl'
LSTM_PATH     = 'model_lstm.pt'
TEXTCNN_PATH  = 'model_textcnn.pt'
LSTM_FT_PATH  = 'model_lstm_fasttext.pt'
FASTTEXT_PATH = 'C:/nlp/cc.ko.300.bin'  # ← 본인 경로로 수정

EMBED_DIM    = 128
HIDDEN_DIM   = 256
NUM_LAYERS   = 2
DROPOUT      = 0.5
MAX_LEN      = 300
NUM_FILTERS  = 128
FILTER_SIZES = [2, 3, 4]
FT_EMBED_DIM = 300

# 앙상블 최적 가중치
W_SVM  = 0.1
W_LSTM = 0.5
W_CNN  = 0.3
W_FT   = 0.1

DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# ─────────────────────────────────────────
# 기술명 정규화 사전
# ─────────────────────────────────────────

TECH_NORMALIZE = {
    r'\bpython\b|\b파이썬\b': 'Python',
    r'\bpytorch\b|\bpyTorch\b|\b파이토치\b': 'PyTorch',
    r'\btensorflow\b|\btensorFlow\b|\b텐서플로\b|\b텐서플로우\b': 'TensorFlow',
    r'\breact\.js\b|\breactjs\b|\breact\b': 'React',
    r'\bnext\.js\b|\bnextjs\b|\bnext js\b': 'Nextjs',
    r'\bvue\.js\b|\bvuejs\b|\bvue\b': 'Vue',
    r'\btypescript\b': 'TypeScript',
    r'\bjavascript\b': 'JavaScript',
    r'\bspring boot\b|\bspringboot\b|\bspring\b': 'SpringBoot',
    r'\bjava\b|\b자바\b': 'Java',
    r'\bkotlin\b|\b코틀린\b': 'Kotlin',
    r'\bnode\.js\b|\bnodejs\b|\bnode js\b': 'Nodejs',
    r'\bdocker\b|\b도커\b': 'Docker',
    r'\bkubernetes\b|\bk8s\b|\b쿠버네티스\b': 'Kubernetes',
    r'\baws\b|\bamazon web services\b': 'AWS',
    r'\bgcp\b|\bgoogle cloud\b': 'GCP',
    r'\bazure\b|\bmicrosoft azure\b': 'Azure',
    r'\bmysql\b|\bpostgresql\b|\bpostgres\b|\bsql\b': 'SQL',
    r'\bmongodb\b|\bmongo\b': 'MongoDB',
    r'\bredis\b': 'Redis',
    r'\bgithub\b|\bgitlab\b|\bgit\b': 'Git',
    r'\bci/cd\b|\bcicd\b|\bci cd\b': 'CICD',
    r'\bmlops\b|\bml ops\b': 'MLOps',
    r'\bllm\b|\blarge language model\b|\b대규모 언어 모델\b': 'LLM',
    r'\brag\b|\bretrieval augmented generation\b': 'RAG',
    r'\bnlp\b|\b자연어 처리\b|\b자연어처리\b': 'NLP',
    r'\bcomputer vision\b|\b컴퓨터 비전\b|\b컴퓨터비전\b': 'ComputerVision',
    r'\btableau\b|\b태블로\b': 'Tableau',
    r'\brest api\b|\brestful api\b|\brestful\b': 'RESTAPI',
    r'\bpandas\b|\b판다스\b': 'Pandas',
    r'\bscikit-learn\b|\bsklearn\b': 'ScikitLearn',
    r'\bairflow\b': 'Airflow',
    r'\bpower bi\b|\bpowerbi\b|\bpbi\b': 'PowerBI',
    r'\bspark\b|\b스파크\b': 'Spark',
    r'\bhive\b': 'Hive',
    r'\bhadoop\b': 'Hadoop',
    r'\bab테스트\b|\ba/b test\b|\ba/b\b|\babt\b': 'ABTest',
    r'\blooker\b': 'Looker',
    r'\bmetabase\b': 'Metabase',
    r'\bsuperset\b': 'Superset',
    r'\b통계\b': '통계분석',
    r'\b마케팅\b': '마케팅분석',
    r'\b지표\b': '데이터지표',
    r'\b데이터\s*파이프라인\b': '데이터파이프라인',
    r'\b데이터\s*웨어하우스\b|\bdwh\b|\bdw\b': '데이터웨어하우스',
    r'\b대시보드\b': '대시보드시각화',
    r'\b시각화\b': '데이터시각화',
}

STOPWORDS = {
    '있', '수', '및', '등', '이', '가', '을', '를', '은', '는',
    '에', '의', '로', '으로', '와', '과', '도', '만', '에서',
    '하다', '하는', '하고', '합니다', '있습니다', '있으며',
    '통해', '위해', '위한', '대한', '관련', '기반', '분', '경험',
    '능력', '역량', '업무', '개발', '서비스', '시스템', '환경',
    '이상', '이하', '담당', '운영', '구축', '설계',
    '분야', '직무', '지원', '채용', '신입', '경력', '인턴',
    '우대', '필수', '자격', '요건', '사항', '내용', '방법',
}

# ─────────────────────────────────────────
# 전처리 함수
# ─────────────────────────────────────────

def normalize_tech(text):
    for pattern, replacement in TECH_NORMALIZE.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text

def tokenize(text, okt):
    if not isinstance(text, str):
        return ''
    text = normalize_tech(text)
    tokens = okt.pos(text, norm=True, stem=True)
    result = []
    for word, pos in tokens:
        if pos in ('Noun', 'Alpha', 'Foreign') and word not in STOPWORDS and len(word) > 1:
            result.append(word)
    return ' '.join(result)

# ─────────────────────────────────────────
# 모델 정의
# ─────────────────────────────────────────

class LSTMClassifier(nn.Module):
    def __init__(self, vocab_size, embed_dim, hidden_dim, num_layers, num_classes, dropout):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.lstm = nn.LSTM(embed_dim, hidden_dim, num_layers=num_layers,
                            batch_first=True, dropout=dropout if num_layers > 1 else 0,
                            bidirectional=True)
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(hidden_dim * 2, num_classes)
    def forward(self, x):
        embedded = self.dropout(self.embedding(x))
        _, (hidden, _) = self.lstm(embedded)
        hidden = torch.cat([hidden[-2], hidden[-1]], dim=1)
        return self.fc(self.dropout(hidden))

class TextCNN(nn.Module):
    def __init__(self, vocab_size, embed_dim, num_filters, filter_sizes, num_classes, dropout):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.convs = nn.ModuleList([
            nn.Conv1d(embed_dim, num_filters, fs) for fs in filter_sizes
        ])
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(num_filters * len(filter_sizes), num_classes)
    def forward(self, x):
        embedded = self.embedding(x).permute(0, 2, 1)
        pooled = [torch.relu(conv(embedded)).max(dim=2).values for conv in self.convs]
        return self.fc(self.dropout(torch.cat(pooled, dim=1)))

class LSTMFastText(nn.Module):
    def __init__(self, vocab_size, embed_dim, hidden_dim, num_layers,
                 num_classes, dropout, embedding_matrix):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.embedding.weight.data.copy_(torch.FloatTensor(embedding_matrix))
        self.embedding.weight.requires_grad = True
        self.lstm = nn.LSTM(embed_dim, hidden_dim, num_layers=num_layers,
                            batch_first=True, dropout=dropout if num_layers > 1 else 0,
                            bidirectional=True)
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(hidden_dim * 2, num_classes)
    def forward(self, x):
        embedded = self.dropout(self.embedding(x))
        _, (hidden, _) = self.lstm(embedded)
        hidden = torch.cat([hidden[-2], hidden[-1]], dim=1)
        return self.fc(self.dropout(hidden))

# ─────────────────────────────────────────
# 모델 로드 (최초 1회만 실행)
# ─────────────────────────────────────────

print('[모델 로드 중...]')

with open(DATA_PATH, 'rb') as f:
    data = pickle.load(f)

X_train = data['X_train']
y_train = data['y_train']

# 어휘 사전
counter = Counter()
for text in X_train:
    counter.update(text.split())
vocab    = ['<PAD>', '<UNK>'] + [w for w, c in counter.items() if c >= 1]
word2idx = {w: i for i, w in enumerate(vocab)}

# 레이블 인코더
le = LabelEncoder()
le.fit(y_train)
NUM_CLASSES = len(le.classes_)

def encode(text, max_len=MAX_LEN):
    tokens = text.split()[:max_len]
    return [word2idx.get(t, word2idx['<UNK>']) for t in tokens]

# Okt 초기화 (최초 1회)
from konlpy.tag import Okt
okt = Okt()
print('Okt 초기화 완료!')

# FastText 임베딩
print('[FastText 로드 중...] (1~2분 소요)')
ft_vectors = load_facebook_vectors(FASTTEXT_PATH)
embedding_matrix = np.zeros((len(vocab), FT_EMBED_DIM))
for word, idx in word2idx.items():
    if word in ft_vectors:
        embedding_matrix[idx] = ft_vectors[word]
print('FastText 로드 완료!')

# 각 모델 로드
svm_model = joblib.load(SVM_PATH)

lstm_model = LSTMClassifier(len(vocab), EMBED_DIM, HIDDEN_DIM, NUM_LAYERS, NUM_CLASSES, DROPOUT).to(DEVICE)
lstm_model.load_state_dict(torch.load(LSTM_PATH, map_location=DEVICE))
lstm_model.eval()

cnn_model = TextCNN(len(vocab), EMBED_DIM, NUM_FILTERS, FILTER_SIZES, NUM_CLASSES, DROPOUT).to(DEVICE)
cnn_model.load_state_dict(torch.load(TEXTCNN_PATH, map_location=DEVICE))
cnn_model.eval()

lstm_ft_model = LSTMFastText(len(vocab), FT_EMBED_DIM, HIDDEN_DIM, NUM_LAYERS,
                              NUM_CLASSES, DROPOUT, embedding_matrix).to(DEVICE)
lstm_ft_model.load_state_dict(torch.load(LSTM_FT_PATH, map_location=DEVICE))
lstm_ft_model.eval()

print('모든 모델 로드 완료!')

# ─────────────────────────────────────────
# predict 함수
# ─────────────────────────────────────────

def predict(text: str) -> dict:
    """
    채용공고 텍스트를 입력하면 직무군과 확률을 반환합니다.

    Args:
        text: 채용공고 텍스트 (title + full_text 합친 것 권장)

    Returns:
        {
            'predicted_job': 'backend',
            'probabilities': {
                'ai': 0.05,
                'backend': 0.82,
                'data_analyst': 0.08,
                'frontend': 0.05
            }
        }
    """
    # 전처리
    tokenized = tokenize(text, okt)

    # TF-IDF + SVM 확률
    svm_proba = svm_model.predict_proba([tokenized])[0]
    svm_classes = svm_model.classes_
    svm_aligned = np.zeros(NUM_CLASSES)
    for i, cls in enumerate(svm_classes):
        j = list(le.classes_).index(cls)
        svm_aligned[j] = svm_proba[i]

    # LSTM / Text-CNN / FastText LSTM 확률
    encoded = torch.tensor(encode(tokenized), dtype=torch.long).unsqueeze(0).to(DEVICE)
    with torch.no_grad():
        lstm_proba = torch.softmax(lstm_model(encoded), dim=1).cpu().numpy()[0]
        cnn_proba  = torch.softmax(cnn_model(encoded), dim=1).cpu().numpy()[0]
        ft_proba   = torch.softmax(lstm_ft_model(encoded), dim=1).cpu().numpy()[0]

    # Soft Voting
    ensemble = W_SVM * svm_aligned + W_LSTM * lstm_proba + W_CNN * cnn_proba + W_FT * ft_proba
    pred_idx = np.argmax(ensemble)
    pred_job = le.classes_[pred_idx]

    return {
        'predicted_job': pred_job,
        'probabilities': {cls: round(float(ensemble[i]), 4) for i, cls in enumerate(le.classes_)}
    }

# ─────────────────────────────────────────
# 테스트 (Test 데이터셋 43개)
# ─────────────────────────────────────────

if __name__ == '__main__':
    import pandas as pd

    print('=== Test 데이터셋 (43개) 정확도 테스트 ===\n')

    X_test = data['X_test']
    y_test = data['y_test']

    # tokenized → input_text 매핑
    preprocessed_df = pd.read_csv('preprocessed_df.csv', encoding='utf-8-sig')
    tokenized_to_input = dict(zip(preprocessed_df['tokenized'], preprocessed_df['input_text']))
    X_test_raw = [tokenized_to_input.get(t, t) for t in X_test]

    correct = 0
    results = []

    for text, true_label in zip(X_test_raw, y_test):
        result = predict(text)
        pred_label = result['predicted_job']
        is_correct = pred_label == true_label
        if is_correct:
            correct += 1
        results.append({'true': true_label, 'pred': pred_label, 'correct': is_correct})

    # 전체 정확도
    print(f'정확도: {correct}/{len(y_test)} ({correct/len(y_test)*100:.1f}%)\n')

    # 오분류 케이스
    print('=== 오분류 케이스 ===')
    for r in results:
        if not r['correct']:
            print(f'  실제: {r["true"]} | 예측: {r["pred"]}')

    # 직무별 정확도
    print('\n=== 직무별 정확도 ===')
    job_total   = Counter(y_test)
    job_correct = Counter([r['true'] for r in results if r['correct']])
    for job in sorted(job_total.keys()):
        acc = job_correct[job] / job_total[job]
        print(f'  {job}: {job_correct[job]}/{job_total[job]} ({acc*100:.1f}%)')