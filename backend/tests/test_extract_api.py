import unittest

from fastapi.testclient import TestClient

from app.main import app


class ExtractApiTest(unittest.TestCase):
    def test_extract_job_posting_from_text(self) -> None:
        client = TestClient(app)
        response = client.post(
            "/extract/job-posting",
            json={
                "source_type": "text",
                "text": "  백엔드 개발자 채용. Docker 배포 경험 필수.  ",
            },
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["kind"], "job_posting")
        self.assertEqual(body["source_type"], "text")
        self.assertEqual(body["text"], "백엔드 개발자 채용. Docker 배포 경험 필수.")
        self.assertEqual(body["extractor"], "direct_text")

    def test_extract_candidate_material_from_txt_file(self) -> None:
        client = TestClient(app)
        response = client.post(
            "/extract/candidate-material",
            data={
                "source_type": "file",
                "label": "이력서",
            },
            files={
                "file": (
                    "resume.txt",
                    "Spring Boot API 개발 및 Docker 배포 경험".encode("utf-8"),
                    "text/plain",
                )
            },
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["kind"], "candidate_material")
        self.assertEqual(body["label"], "이력서")
        self.assertEqual(body["source_type"], "txt")
        self.assertIn("Spring Boot", body["text"])

    def test_candidate_material_rejects_url_source(self) -> None:
        client = TestClient(app)
        response = client.post(
            "/extract/candidate-material",
            json={
                "source_type": "url",
                "url": "https://example.com/profile",
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("URL", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
