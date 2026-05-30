from __future__ import annotations

import unittest

import numpy as np

from app.services.c_part import pipeline


SKILL_INDEX = {
    "spring boot": 0,
    "docker": 1,
    "aws": 2,
    "kubernetes": 3,
    "junit": 4,
}


def fake_embedding(text: str) -> np.ndarray:
    vector = np.zeros(len(SKILL_INDEX), dtype=float)
    lowered = text.lower()
    for token, index in SKILL_INDEX.items():
        if token in lowered:
            vector[index] = 1.0
    if not vector.any():
        vector[-1] = 0.1
    return vector


class CPartPipelineTest(unittest.TestCase):
    def setUp(self) -> None:
        self.original_get_embedding = pipeline.get_embedding
        pipeline.get_embedding = fake_embedding

    def tearDown(self) -> None:
        pipeline.get_embedding = self.original_get_embedding

    def test_long_text_loads_as_text_not_path(self) -> None:
        text = "채용공고 본문입니다. " * 500
        self.assertEqual(pipeline.load_text(text), text)

    def test_fit_score_counts_partial_as_half(self) -> None:
        """
        필수 Docker(coverage=85), 우대 AWS(coverage=50) →
        fit_score = 85 × 0.7 + 50 × 0.3 = 59.5 + 15.0 = 74.5 → 75
        """
        from app.services.c_part.pipeline import _compute_fit_score
        required = ["Docker", "AWS"]
        coverage_map = {"Docker": 85.0, "AWS": 50.0}
        importance_map = {"Docker": "필수", "AWS": "우대"}
        score = _compute_fit_score(required, coverage_map, importance_map)
        self.assertAlmostEqual(score, 75, delta=2)

    def test_outputs_owned_partial_and_gaps_without_overlap(self) -> None:
        result = pipeline.run_c_part_analysis(
            b_predicted_job="backend",
            jd_input=(
                "Spring Boot 개발 경험이 필수입니다. "
                "Docker 운영 경험이 필수입니다. "
                "AWS 배포 경험이 있으면 우대합니다."
            ),
            candidate_input=(
                "Spring Boot 기반 REST API를 설계하고 구현했습니다. "
                "AWS EC2를 간단히 사용해 본 경험이 있습니다. "
                "Docker는 들어본 적 있습니다."
            ),
            threshold=1.1,
        )
        self.assertEqual(result["status"], "success")
        owned = {item["skill"] for item in result["owned_skills"]}
        partial = {item["skill"] for item in result["partial_skills"]}
        gaps = {item["skill"] for item in result["skill_gaps"]}
        # coverage 기반 분류: 세 목록이 서로 겹치지 않으면 충분
        self.assertFalse(owned & partial)
        self.assertFalse(owned & gaps)
        self.assertFalse(partial & gaps)

    def test_extract_required_skills_no_overextraction(self) -> None:
        """JD에 명시되지 않은 스킬이 required_skills에 포함되지 않아야 한다."""
        from app.services.c_part import pipeline as _pl
        from app.services.c_part.pipeline import (
            extract_required_skills,
            split_sentences,
        )

        # 실제 임베딩 모델이 필요한 테스트 — fake embedding을 잠시 복원
        _pl.get_embedding = self.original_get_embedding
        get_embedding = self.original_get_embedding

        jd_text = (
            "Spring Boot 기반 REST API 개발 경험 필수.\n"
            "MySQL 데이터 모델링 및 쿼리 최적화.\n"
            "Docker 컨테이너 배포 경험 필요.\n"
            "AWS 클라우드 운영. CI/CD 파이프라인 구축."
        )
        jd_sentences = split_sentences(jd_text)
        jd_vectors = [get_embedding(s) for s in jd_sentences]

        result = extract_required_skills("backend", jd_sentences, jd_vectors)
        skill_names = [r["skill"] for r in result]

        # JD에 명시된 기술은 포함
        assert "Spring Boot" in skill_names, f"Spring Boot 누락: {skill_names}"
        assert "REST API" in skill_names, f"REST API 누락: {skill_names}"
        assert "MySQL" in skill_names, f"MySQL 누락: {skill_names}"
        assert "Docker" in skill_names, f"Docker 누락: {skill_names}"

        # JD에 없는 기술은 포함 불가
        assert "Java" not in skill_names, f"Java 과다 추출: {skill_names}"
        assert "Kotlin" not in skill_names, f"Kotlin 과다 추출: {skill_names}"
        assert "OpenAPI" not in skill_names, f"OpenAPI 과다 추출: {skill_names}"
        assert "PostgreSQL" not in skill_names, f"PostgreSQL 과다 추출: {skill_names}"
        assert "Node.js" not in skill_names, f"Node.js 과다 추출: {skill_names}"
        assert "JUnit" not in skill_names, f"JUnit 과다 추출: {skill_names}"

    def test_extract_required_skills_korean_aliases(self) -> None:
        """한국어 기술명 JD에서 정규화된 영문명으로 추출되어야 한다."""
        from app.services.c_part import pipeline as _pl
        from app.services.c_part.pipeline import (
            extract_required_skills,
            split_sentences,
        )

        # 실제 임베딩 모델이 필요한 테스트 — fake embedding을 잠시 복원
        _pl.get_embedding = self.original_get_embedding
        get_embedding = self.original_get_embedding

        jd_text = (
            "스프링 부트 기반 백엔드 개발 경험 3년 이상 필수.\n"
            "도커를 활용한 컨테이너 배포 경험.\n"
            "쿠버네티스 운영 경험 우대."
        )
        jd_sentences = split_sentences(jd_text)
        jd_vectors = [get_embedding(s) for s in jd_sentences]

        result = extract_required_skills("backend", jd_sentences, jd_vectors)
        skill_names = [r["skill"] for r in result]

        assert "Spring Boot" in skill_names, (
            f"'스프링 부트' → 'Spring Boot' alias 매칭 실패: {skill_names}"
        )
        assert "Docker" in skill_names, (
            f"'도커' → 'Docker' alias 매칭 실패: {skill_names}"
        )
        assert "Kubernetes" in skill_names, (
            f"'쿠버네티스' → 'Kubernetes' alias 매칭 실패: {skill_names}"
        )

    def test_keyword_hit_word_boundary_no_false_positive(self) -> None:
        """Java/Git 등이 JavaScript/GitHub에서 잘못 매칭되지 않아야 한다."""
        from app.services.c_part.pipeline import _keyword_hit_any

        # word-boundary: 이전 substring 방식의 false positive 케이스
        assert not _keyword_hit_any("Java", "JavaScript TypeScript 개발 경험"), \
            "Java must not match inside JavaScript"
        assert not _keyword_hit_any("Git", "GitHub Actions, GitLab CI/CD 사용"), \
            "Git must not match inside GitHub/GitLab"

        # 정상 매칭: 단어 경계에서 정확히 있는 경우
        assert _keyword_hit_any("Java", "Java와 Spring Boot 기반 REST API 개발"), \
            "Java exact match must pass"
        assert _keyword_hit_any("Git", "Git, SVN 버전 관리 경험 보유"), \
            "Git exact match must pass"

    def test_coverage_boundary_39_is_missing(self) -> None:
        from app.services.c_part.pipeline import _coverage_level
        self.assertEqual(_coverage_level(39.9)[0], "missing")

    def test_coverage_boundary_40_is_partial(self) -> None:
        from app.services.c_part.pipeline import _coverage_level
        self.assertEqual(_coverage_level(40.0)[0], "partial")

    def test_coverage_boundary_69_is_partial(self) -> None:
        from app.services.c_part.pipeline import _coverage_level
        self.assertEqual(_coverage_level(69.9)[0], "partial")

    def test_coverage_boundary_70_is_owned(self) -> None:
        from app.services.c_part.pipeline import _coverage_level
        self.assertEqual(_coverage_level(70.0)[0], "owned")

    def test_exp_bonus_caps_at_100(self) -> None:
        from app.services.c_part.pipeline import _compute_coverage, COV_STRONG
        cov = _compute_coverage(COV_STRONG + 0.1, has_exp_verb=True)
        self.assertLessEqual(cov, 100.0)

    def test_zero_sim_gives_zero_coverage(self) -> None:
        from app.services.c_part.pipeline import _compute_coverage
        cov = _compute_coverage(0.0)
        self.assertEqual(cov, 0.0)

    def test_compute_coverage_monotone(self) -> None:
        """sim 증가 → coverage 비감소."""
        from app.services.c_part.pipeline import _compute_coverage
        sims = [0.0, 0.2, 0.3, 0.5, 0.7, 0.9, 1.0]
        covs = [_compute_coverage(s) for s in sims]
        for i in range(len(covs) - 1):
            self.assertLessEqual(covs[i], covs[i + 1])


if __name__ == "__main__":
    unittest.main()
