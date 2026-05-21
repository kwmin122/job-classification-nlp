from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.services.embedding_retriever import RetrieverInfo


class RecommendApiTest(unittest.TestCase):
    def test_recommend_response_exposes_retrieval_metadata(self) -> None:
        previous_key = os.environ.pop("OPENAI_API_KEY", None)
        try:
            client = TestClient(app)
            sample = client.get("/sample").json()

            response = client.post("/recommend", json=sample)

            self.assertEqual(response.status_code, 200)
            body = response.json()
            self.assertEqual(body["retrieval_mode"], "tfidf_fallback")
            self.assertEqual(body["embedding_model"], "none")
            self.assertEqual(body["chunking_strategy"], "one_resource_row_per_chunk")
        finally:
            if previous_key is not None:
                os.environ["OPENAI_API_KEY"] = previous_key

    def test_recommend_falls_back_when_embedding_search_fails(self) -> None:
        class BrokenRetriever:
            def search(self, query: str, limit: int = 8):
                raise RuntimeError("embedding API failed")

        client = TestClient(app)
        sample = client.get("/sample").json()

        with patch(
            "app.main.build_retriever",
            return_value=(
                BrokenRetriever(),
                RetrieverInfo(
                    retrieval_mode="embedding",
                    embedding_model="text-embedding-3-small",
                    chunking_strategy="one_resource_row_per_chunk",
                ),
            ),
        ):
            response = client.post("/recommend", json=sample)

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["retrieval_mode"], "tfidf_fallback")
        self.assertEqual(body["embedding_model"], "none")


if __name__ == "__main__":
    unittest.main()
