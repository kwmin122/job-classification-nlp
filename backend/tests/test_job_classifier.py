import unittest
from pathlib import Path
from unittest.mock import patch

from app.services.job_classifier import MODEL_DIR, classify_job, load_classifier_bundle


class JobClassifierTest(unittest.TestCase):
    def test_ab_artifacts_exist(self) -> None:
        expected = [
            "model_tfidf_svm.pkl",
            "model_lstm.pt",
            "model_textcnn.pt",
            "model_lstm_fasttext.pt",
            "preprocessed_data.pkl",
        ]
        for name in expected:
            self.assertTrue((Path(MODEL_DIR) / name).exists(), name)

    def test_loader_uses_checkpoint_without_fasttext_bin_path(self) -> None:
        load_classifier_bundle.cache_clear()
        with patch.dict("os.environ", {}, clear=True):
            bundle = load_classifier_bundle()
        self.assertEqual(len(bundle.word2idx), 4168)
        self.assertEqual(tuple(bundle.fasttext_lstm_model.embedding.weight.shape), (4168, 300))

    def test_classify_job_returns_korean_job_name(self) -> None:
        result = classify_job(
            "백엔드 개발자 채용. Spring Boot REST API 개발과 Docker 기반 배포 경험 필수."
        )
        self.assertIn(
            result.predicted_job,
            ["AI/ML 엔지니어", "백엔드 개발자", "데이터 분석가", "프론트엔드 개발자"],
        )
        self.assertEqual(
            set(result.job_probabilities),
            {"AI/ML 엔지니어", "백엔드 개발자", "데이터 분석가", "프론트엔드 개발자"},
        )
        self.assertEqual(result.classifier_source, "ab_ensemble")
