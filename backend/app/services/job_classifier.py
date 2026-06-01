from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import pickle

import joblib
import numpy as np
from sklearn.preprocessing import LabelEncoder
import torch

from app.services.job_classifier_models import LSTMClassifier, LSTMFastText, TextCNN
from app.services.job_label_mapping import LABEL_ORDER, to_job_name
from app.services.job_preprocessor import preprocess_for_job_classifier


MODEL_DIR = Path(__file__).resolve().parents[1] / "models" / "job_classifier"

EMBED_DIM = 128
HIDDEN_DIM = 256
NUM_LAYERS = 2
DROPOUT = 0.5
MAX_LEN = 300
NUM_FILTERS = 128
FILTER_SIZES = [2, 3, 4]
FT_EMBED_DIM = 300
EXPECTED_VOCAB_SIZE = 4168

WEIGHTS = {
    "svm": 0.1,
    "lstm": 0.5,
    "textcnn": 0.3,
    "fasttext_lstm": 0.1,
}


@dataclass(frozen=True)
class JobClassification:
    predicted_job: str
    job_label: str
    job_probabilities: dict[str, float]
    classifier_source: str


@dataclass
class ClassifierBundle:
    svm_model: object
    lstm_model: LSTMClassifier
    textcnn_model: TextCNN
    fasttext_lstm_model: LSTMFastText
    word2idx: dict[str, int]
    label_encoder: LabelEncoder
    device: torch.device


def _build_vocab(texts: list[str]) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for text in texts:
        counter.update(text.split())
    vocab = ["<PAD>", "<UNK>"] + [word for word, count in counter.items() if count >= 1]
    return {word: index for index, word in enumerate(vocab)}


def _encode(text: str, word2idx: dict[str, int]) -> list[int]:
    tokens = text.split()[:MAX_LEN]
    encoded = [word2idx.get(token, word2idx["<UNK>"]) for token in tokens]
    min_len = max(FILTER_SIZES)
    if len(encoded) < min_len:
        encoded.extend([word2idx["<PAD>"]] * (min_len - len(encoded)))
    return encoded


def _align_probabilities(classes: list[str], probabilities: np.ndarray) -> np.ndarray:
    aligned = np.zeros(len(LABEL_ORDER), dtype=float)
    for index, label in enumerate(classes):
        aligned[LABEL_ORDER.index(label)] = float(probabilities[index])
    return aligned


@lru_cache(maxsize=1)
def load_classifier_bundle() -> ClassifierBundle:
    with (MODEL_DIR / "preprocessed_data.pkl").open("rb") as file:
        data = pickle.load(file)

    x_train = data["X_train"]
    y_train = data["y_train"]
    word2idx = _build_vocab(x_train)

    label_encoder = LabelEncoder()
    label_encoder.fit(y_train)
    if list(label_encoder.classes_) != LABEL_ORDER:
        raise ValueError(f"Unexpected label order: {list(label_encoder.classes_)}")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    num_classes = len(label_encoder.classes_)
    vocab_size = len(word2idx)
    if vocab_size != EXPECTED_VOCAB_SIZE:
        raise ValueError(
            f"Unexpected vocab size: {vocab_size}. "
            f"Expected {EXPECTED_VOCAB_SIZE} from A/B preprocessed_data.pkl."
        )

    svm_model = joblib.load(MODEL_DIR / "model_tfidf_svm.pkl")

    lstm_model = LSTMClassifier(
        vocab_size,
        EMBED_DIM,
        HIDDEN_DIM,
        NUM_LAYERS,
        num_classes,
        DROPOUT,
    ).to(device)
    lstm_model.load_state_dict(torch.load(MODEL_DIR / "model_lstm.pt", map_location=device))
    lstm_model.eval()

    textcnn_model = TextCNN(
        vocab_size,
        EMBED_DIM,
        NUM_FILTERS,
        FILTER_SIZES,
        num_classes,
        DROPOUT,
    ).to(device)
    textcnn_model.load_state_dict(torch.load(MODEL_DIR / "model_textcnn.pt", map_location=device))
    textcnn_model.eval()

    fasttext_lstm_model = LSTMFastText(
        vocab_size,
        FT_EMBED_DIM,
        HIDDEN_DIM,
        NUM_LAYERS,
        num_classes,
        DROPOUT,
    ).to(device)
    fasttext_lstm_model.load_state_dict(
        torch.load(MODEL_DIR / "model_lstm_fasttext.pt", map_location=device)
    )
    if tuple(fasttext_lstm_model.embedding.weight.shape) != (EXPECTED_VOCAB_SIZE, FT_EMBED_DIM):
        raise ValueError(
            "Unexpected FastText LSTM embedding shape: "
            f"{tuple(fasttext_lstm_model.embedding.weight.shape)}"
        )
    fasttext_lstm_model.eval()

    return ClassifierBundle(
        svm_model=svm_model,
        lstm_model=lstm_model,
        textcnn_model=textcnn_model,
        fasttext_lstm_model=fasttext_lstm_model,
        word2idx=word2idx,
        label_encoder=label_encoder,
        device=device,
    )


def classify_job(text: str) -> JobClassification:
    bundle = load_classifier_bundle()
    tokenized = preprocess_for_job_classifier(text)

    svm_proba = bundle.svm_model.predict_proba([tokenized])[0]
    svm_aligned = _align_probabilities(list(bundle.svm_model.classes_), svm_proba)

    encoded = torch.tensor(
        _encode(tokenized, bundle.word2idx),
        dtype=torch.long,
        device=bundle.device,
    ).unsqueeze(0)

    with torch.no_grad():
        lstm_proba = torch.softmax(bundle.lstm_model(encoded), dim=1).cpu().numpy()[0]
        cnn_proba = torch.softmax(bundle.textcnn_model(encoded), dim=1).cpu().numpy()[0]
        ft_proba = torch.softmax(bundle.fasttext_lstm_model(encoded), dim=1).cpu().numpy()[0]

    ensemble = (
        WEIGHTS["svm"] * svm_aligned
        + WEIGHTS["lstm"] * lstm_proba
        + WEIGHTS["textcnn"] * cnn_proba
        + WEIGHTS["fasttext_lstm"] * ft_proba
    )
    pred_index = int(np.argmax(ensemble))
    label = LABEL_ORDER[pred_index]

    return JobClassification(
        predicted_job=to_job_name(label),
        job_label=label,
        job_probabilities={
            to_job_name(label_name): round(float(ensemble[index]), 4)
            for index, label_name in enumerate(LABEL_ORDER)
        },
        classifier_source="ab_ensemble",
    )
